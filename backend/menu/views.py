from rest_framework.generics import ListAPIView

from .models import Category
from .serializers import CategorySerializer


class MenuView(ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.prefetch_related("items__modifier_group__options")
