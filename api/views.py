from django.shortcuts import render
from django.http import JsonResponse

from core.models import Book
from core.utils import clean_isbn

from .serializers import BookSerializer


def book_by_isbn(request):
    raw_isbn = request.GET.get("isbn")
    if not raw_isbn:
        return JsonResponse({"detail": "No 'isbn' parameter given."})

    isbn = clean_isbn(raw_isbn)
    if not isbn:
        return JsonResponse({"detail": f"ISBN {raw_isbn} is not valid ISBN."})

    book = Book.objects.filter(isbn=isbn).first()
    if book:
        serializer = BookSerializer(book)
        return JsonResponse(serializer.data)
    return JsonResponse({"detail": "No book found."}, status=404)
