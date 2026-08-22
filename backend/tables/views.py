from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import OrderSerializer

from .models import Table
from .serializers import TableLocationSerializer, TableSerializer


class TableListView(ListAPIView):
    serializer_class = TableSerializer
    queryset = Table.objects.all()


class TableOpenOrderView(APIView):
    def post(self, request, pk):
        table = get_object_or_404(Table, pk=pk)
        order = table.open_order
        if order is None:
            order = Order.objects.create(table=table, opened_by=request.user)
        return Response(OrderSerializer(order).data)


class TableLocationView(APIView):
    """Sets/clears the free-text note on a helper table (e.g. "F3") saying
    which physical table its food should actually be delivered to."""

    def patch(self, request, pk):
        table = get_object_or_404(Table, pk=pk)
        serializer = TableLocationSerializer(table, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TableSerializer(table).data)
