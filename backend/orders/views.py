from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CashRegisterEntry, Order, OrderItem
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
    the order is paid, the order itself auto-closes and the table frees up."""

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
        items_to_pay = unpaid.filter(id__in=[i.id for i in requested_items]) if requested_items else unpaid

        paid_item_ids = list(items_to_pay.values_list("id", flat=True))
        if not paid_item_ids:
            return Response({"detail": "Nothing to pay."}, status=status.HTTP_400_BAD_REQUEST)

        items_to_pay.update(is_paid=True, paid_at=timezone.now(), payment_method=payment_method)

        if not order.items.filter(is_paid=False).exists():
            order.status = "PAID"
            order.closed_at = timezone.now()
            order.save(update_fields=["status", "closed_at"])

        response_data = OrderSerializer(order).data
        response_data["paid_item_ids"] = paid_item_ids
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

        today = timezone.localdate()

        daily = list(
            paid_items.annotate(day=TruncDate("paid_at"))
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
    """The till float ('polog') plus cash/card totals taken in since it was
    last set — anyone signed in can view it (a waiter should be able to
    check it), but only an admin can set a new float (POST)."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return super().get_permissions()

    def get(self, request):
        latest = CashRegisterEntry.objects.select_related("set_by").first()
        float_amount = latest.float_amount if latest else Decimal("0.00")
        since = latest.set_at if latest else None

        line_total = ExpressionWrapper(
            F("unit_price") * F("quantity"), output_field=DecimalField(max_digits=10, decimal_places=2)
        )
        paid_since = OrderItem.objects.filter(is_paid=True)
        if since:
            paid_since = paid_since.filter(paid_at__gte=since)

        def total_for(method):
            return paid_since.filter(payment_method=method).aggregate(total=Sum(line_total))["total"] or Decimal("0.00")

        cash_total = total_for("CASH")
        card_total = total_for("CARD")

        data = {
            "float_amount": float_amount,
            "set_at": since,
            "set_by_username": latest.set_by.username if latest and latest.set_by else None,
            "cash_total": cash_total,
            "card_total": card_total,
            "expected_cash": float_amount + cash_total,
        }
        return Response(CashRegisterStateSerializer(data).data)

    def post(self, request):
        serializer = SetCashFloatSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request)
