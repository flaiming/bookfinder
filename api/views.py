from django.db.models import Count, Q, Min, Max
from django.shortcuts import render
from django.http import JsonResponse

from core.models import Book, BookPriceType
from core.utils import clean_isbn

from .serializers import BookSerializer


def book_by_isbn(request):
    raw_isbn = request.GET.get("isbn")
    if not raw_isbn:
        return JsonResponse({"detail": "No 'isbn' parameter given."}, status=400)

    isbn = clean_isbn(raw_isbn)
    if not isbn:
        return JsonResponse({"detail": f"ISBN {raw_isbn} is not valid ISBN."}, status=402)

    queryset = Book.objects.with_prices()
    book = queryset.filter(isbn=isbn).first()
    if book:
        serializer = BookSerializer(book)
        return JsonResponse(serializer.data)
    return JsonResponse({"detail": "No book found."}, status=404)
