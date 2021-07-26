from django.contrib import admin
from .models import Book, BookCover, Author, BookImport, BookPrice, BookProfile


class BookCoverInline(admin.TabularInline):
    model = BookCover
    readonly_fields = ["profile"]
    extra = 0


class BookPriceInline(admin.TabularInline):
    model = BookPrice
    fields = ["id", "price_type", "price", "profile", "source", "orig_id", "created", "updated"]
    readonly_fields = ["profile", "book", "source", "created", "updated"]
    extra = 0


class BookProfileInline(admin.TabularInline):
    model = BookProfile.books.through
    fields = ["bookprofile"]
    extra = 0
    readonly_fields = ["bookprofile"]


class BookAdmin(admin.ModelAdmin):
    readonly_fields = ["authors"]
    list_display = ["name", "isbn", "year", "pages"]
    search_fields = ["name"]
    inlines = [BookCoverInline, BookPriceInline, BookProfileInline]
    exclude = ["profiles"]


class AuthorAdmin(admin.ModelAdmin):
    search_fields = ["name"]


admin.site.register(Book, BookAdmin)
admin.site.register(Author, AuthorAdmin)


class BookImportAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name", "active", "price_type"]


admin.site.register(BookImport, BookImportAdmin)
