from django.urls import path

from .views import TableListView, TableOpenOrderView

urlpatterns = [
    path("", TableListView.as_view(), name="table-list"),
    path("<int:pk>/open-order/", TableOpenOrderView.as_view(), name="table-open-order"),
]
