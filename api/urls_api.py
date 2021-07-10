from django.urls import path, include
from rest_framework import routers

from .views_api import BookViewSet
from .views import book_by_isbn

app_name = "api"
router = routers.SimpleRouter()
router.register(r'books', BookViewSet)

urlpatterns = [
    path('book-by-isbn/', book_by_isbn),
] + router.urls
