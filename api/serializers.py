from rest_framework import serializers

from core.models import Book, Author


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = ["id", "name"]


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True)
    price_offer_max = serializers.IntegerField(read_only=True)
    price_request_max = serializers.IntegerField(read_only=True)
    price_new = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "name",
            "other_names",
            "isbn",
            "pages",
            "language",
            "year",
            "authors",
            "price_offer_max",
            "price_request_max",
            "price_new",
            "cover",
        ]

    def get_cover(self, obj):
        cover = ""
        try:
            cover = list(obj.covers.all())[0].image_url
        except IndexError:
            pass
        return cover
