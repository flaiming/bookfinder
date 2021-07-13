from django.db.models import Count, Q, Min, Max
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated

from core.models import Book, BookPriceType
from .serializers import BookSerializer


class BookViewSet(ListModelMixin, GenericViewSet):
    queryset = Book.objects.with_prices()
    serializer_class = BookSerializer
    permission_classes = (IsAuthenticated,)
