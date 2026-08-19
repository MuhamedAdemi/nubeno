from django.urls import path

from .views import (
    AnalyticsView,
    CashRegisterView,
    OrderCancelView,
    OrderDetailView,
    OrderItemCreateView,
    OrderItemDetailView,
    OrderPayView,
    OrderTransferView,
)

urlpatterns = [
    path("analytics/", AnalyticsView.as_view(), name="order-analytics"),
    path("cash-register/", CashRegisterView.as_view(), name="cash-register"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/items/", OrderItemCreateView.as_view(), name="order-item-create"),
    path(
        "<int:pk>/items/<int:item_id>/",
        OrderItemDetailView.as_view(),
        name="order-item-detail",
    ),
    path("<int:pk>/pay/", OrderPayView.as_view(), name="order-pay"),
    path("<int:pk>/transfer/", OrderTransferView.as_view(), name="order-transfer"),
    path("<int:pk>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
]
