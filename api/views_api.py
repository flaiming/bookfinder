from django.db.models import Count, Q, Min, Max
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated

from core.models import Book, BookPriceType
from .serializers import BookSerializer


class BookViewSet(ListModelMixin, GenericViewSet):
    queryset = Book.objects.all()
    queryset = Book.objects.annotate(
        price_offer_max=Max("prices__price", filter=Q(prices__price_type=BookPriceType.OFFER)),
        price_request_max=Max("prices__price", filter=Q(prices__price_type=BookPriceType.REQUEST)),
        price_new=Max("prices__price", filter=Q(prices__price_type=BookPriceType.NEW)),
        # TODO used_price as price from XML
    ).prefetch_related("covers")
    serializer_class = BookSerializer
    permission_classes = (IsAuthenticated,)
