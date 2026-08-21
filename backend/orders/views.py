from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, DateTimeField, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CashRegisterEntry, Order, OrderItem

# The restaurant's "day" rolls over at 7am, not midnight — a payment made
# at 1am is still last night's business, and bucketing it into the next
# calendar day was confusing reconciliation. Shifting by a fixed real-world
# duration before any local-time truncation keeps this correct across DST:
# the shift itself is timezone-naive (always exactly 7 hours), and Django's
# TruncDate/localtime conversion handles the local wall-clock date after
# that shift.
BUSINESS_DAY_START_HOUR = 7


def business_date(dt):
    return (timezone.localtime(dt) - timedelta(hours=BUSINESS_DAY_START_HOUR)).date()


def business_day_start(date):
    """The UTC-aware instant when the given business day began (that date
    at 07:00 local time)."""
    return timezone.make_aware(datetime.combine(date, time(hour=BUSINESS_DAY_START_HOUR)))
from .serializers import (
    AddOrderItemSerializer,
    CashRegisterStateSerializer,
    OrderSerializer,
    PayItemsSerializer,
    SetCashFloatSerializer,
    TransferOrderSerializer,
    UpdateOrderItemSerializer,
)


class OrderDetailView(RetrieveAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("items__menu_item", "items__removed_modifiers")


class OrderItemCreateView(APIView):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status != "OPEN":
            return Response(
                {"detail": "Order is not open."}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = AddOrderItemSerializer(data=request.data, context={"order": order})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderItemDetailView(APIView):
    def patch(self, request, pk, item_id):
        order = get_object_or_404(Order, pk=pk)
        if order.status != "OPEN":
            return Response(
                {"detail": "Order is not open."}, status=status.HTTP_400_BAD_REQUEST
            )
        item = get_object_or_404(OrderItem, pk=item_id, order=order)
        if item.is_paid:
            return Response(
                {"detail": "This item is already paid and can't be changed."}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UpdateOrderItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    def delete(self, request, pk, item_id):
        order = get_object_or_404(Order, pk=pk)
        if order.status != "OPEN":
            return Response(
                {"detail": "Order is not open."}, status=status.HTTP_400_BAD_REQUEST
            )
        item = get_object_or_404(OrderItem, pk=item_id, order=order)
        if item.is_paid:
            return Response(
                {"detail": "This item is already paid and can't be deleted."}, status=status.HTTP_400_BAD_REQUEST
            )
        item.delete()
        return Response(OrderSerializer(order).data)


class OrderPayView(APIView):
    """Pays either the given item_ids (a split/partial payment) or, if none
    are given, every currently-unpaid item on the order. Once every item on
    the order is paid, the order itself auto-closes and the table frees up.

    Every paid item gets a cash_portion (how much of *that item's*
    line_total was cash) regardless of payment_method — CASH -> the whole
    line_total, CARD -> zero, MIXED -> a share of the entered cash_amount
    proportional to the item's share of the batch, with the last item
    absorbing the rounding remainder so the shares always sum exactly to
    cash_amount. This lets CashRegisterView sum one field for all three
    payment methods instead of branching on payment_method."""

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status != "OPEN":
            return Response(
                {"detail": "Order is not open."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PayItemsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requested_items = serializer.validated_data["item_ids"]
        payment_method = serializer.validated_data["payment_method"]

        unpaid = order.items.filter(is_paid=False)
        items_to_pay = list(
            (unpaid.filter(id__in=[i.id for i in requested_items]) if requested_items else unpaid)
        )

        if not items_to_pay:
            return Response({"detail": "Nothing to pay."}, status=status.HTTP_400_BAD_REQUEST)

        batch_total = sum((item.line_total for item in items_to_pay), Decimal("0.00"))

        if payment_method == "CASH":
            for item in items_to_pay:
                item.cash_portion = item.line_total
        elif payment_method == "CARD":
            for item in items_to_pay:
                item.cash_portion = Decimal("0.00")
        else:  # MIXED
            cash_amount = serializer.validated_data["cash_amount"]
            if cash_amount > batch_total:
                return Response(
                    {"detail": "Cash amount can't exceed the total being paid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            allocated = Decimal("0.00")
            for item in items_to_pay[:-1]:
                share = (
                    (item.line_total / batch_total * cash_amount).quantize(Decimal("0.01"))
                    if batch_total
                    else Decimal("0.00")
                )
                item.cash_portion = share
                allocated += share
            items_to_pay[-1].cash_portion = cash_amount - allocated

        now = timezone.now()
        for item in items_to_pay:
            item.is_paid = True
            item.paid_at = now
            item.payment_method = payment_method
        OrderItem.objects.bulk_update(items_to_pay, ["is_paid", "paid_at", "payment_method", "cash_portion"])

        if not order.items.filter(is_paid=False).exists():
            order.status = "PAID"
            order.closed_at = timezone.now()
            order.save(update_fields=["status", "closed_at"])

        response_data = OrderSerializer(order).data
        response_data["paid_item_ids"] = [item.id for item in items_to_pay]
        return Response(response_data)


class OrderTransferView(APIView):
    """Moves an in-progress order (and everything on it) to a different,
    currently-free table — e.g. a guest who started at one table moves to
    another one entirely."""

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status != "OPEN":
            return Response(
                {"detail": "Order is not open."}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = TransferOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order.table = serializer.validated_data["table"]
        order.save(update_fields=["table"])
        return Response(OrderSerializer(order).data)


class OrderCancelView(APIView):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status != "OPEN":
            return Response(
                {"detail": "Order is not open."}, status=status.HTTP_400_BAD_REQUEST
            )
        order.status = "CANCELLED"
        order.closed_at = timezone.now()
        order.save(update_fields=["status", "closed_at"])
        return Response(OrderSerializer(order).data)


class AnalyticsView(APIView):
    """Sales totals for admins only — daily breakdown plus
    today/week/month/all-time summaries. Counted per paid *item* (not per
    closed order), since a split-payment order can stay open for a while
    with some items already paid and others not.

    Waiters get today's turnover from CashRegisterView instead (alongside
    the cash/card split) — this view stays admin-only for the historical,
    multi-day view."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        line_total = ExpressionWrapper(
            F("unit_price") * F("quantity"), output_field=DecimalField(max_digits=10, decimal_places=2)
        )
        paid_items = OrderItem.objects.filter(is_paid=True)

        today = business_date(timezone.now())

        # Shift each paid_at back by the business-day start offset before
        # truncating to date, so a 1am payment still counts as the previous
        # business day instead of the next calendar day.
        shifted = ExpressionWrapper(
            F("paid_at") - timedelta(hours=BUSINESS_DAY_START_HOUR), output_field=DateTimeField()
        )
        daily = list(
            paid_items.annotate(shifted_at=shifted)
            .annotate(day=TruncDate("shifted_at"))
            .values("day")
            .annotate(total=Sum(line_total), order_count=Count("order", distinct=True))
            .order_by("-day")[:60]
        )

        all_time_total = paid_items.aggregate(total=Sum(line_total))["total"] or Decimal("0.00")

        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        def sum_since(start_date):
            return sum((row["total"] for row in daily if row["day"] and row["day"] >= start_date), Decimal("0.00"))

        return Response(
            {
                "today_total": str(sum_since(today)),
                "week_total": str(sum_since(week_start)),
                "month_total": str(sum_since(month_start)),
                "all_time_total": str(all_time_total),
                "daily": [
                    {"date": row["day"].isoformat(), "order_count": row["order_count"], "total": str(row["total"])}
                    for row in daily
                    if row["day"]
                ],
            }
        )


class CashRegisterView(APIView):
    """The till float ('polog') plus today's cash/card totals — anyone
    signed in can view it (a waiter should be able to check it), but only
    an admin can set a new float (POST).

    The float persists across days (it's the fixed change-drawer baseline,
    not a daily reset), but the cash/card totals shown are scoped to the
    current *business day* (see business_date/business_day_start above) —
    the owner wanted "everything for the current day," on the assumption
    the previous day's cash is already removed/reconciled by the time a new
    business day starts."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return super().get_permissions()

    def get(self, request):
        latest = CashRegisterEntry.objects.select_related("set_by").first()
        float_amount = latest.float_amount if latest else Decimal("0.00")

        today = business_date(timezone.now())
        day_start = business_day_start(today)

        line_total = ExpressionWrapper(
            F("unit_price") * F("quantity"), output_field=DecimalField(max_digits=10, decimal_places=2)
        )
        paid_today = OrderItem.objects.filter(is_paid=True, paid_at__gte=day_start)

        # cash_portion is set on every paid item regardless of payment_method
        # (see OrderPayView) — CASH/CARD/MIXED all reduce to the same sum.
        totals = paid_today.aggregate(cash=Sum("cash_portion"), grand_total=Sum(line_total))
        cash_total = totals["cash"] or Decimal("0.00")
        grand_total = totals["grand_total"] or Decimal("0.00")
        card_total = grand_total - cash_total

        data = {
            "float_amount": float_amount,
            "set_at": latest.set_at if latest else None,
            "set_by_username": latest.set_by.username if latest and latest.set_by else None,
            "cash_total": cash_total,
            "card_total": card_total,
            "today_total": grand_total,
            "expected_cash": float_amount + cash_total,
        }
        return Response(CashRegisterStateSerializer(data).data)

    def post(self, request):
        serializer = SetCashFloatSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request)
