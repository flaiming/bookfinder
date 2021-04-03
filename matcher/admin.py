from django.contrib import admin
from matcher.models import Book, BookCover, Author


class BookCoverInline(admin.TabularInline):
    model = BookCover
    extra = 0


class BookAdmin(admin.ModelAdmin):
    readonly_fields = ["authors"]
    search_fields = ["name"]
    inlines = [BookCoverInline]


class AuthorAdmin(admin.ModelAdmin):
    search_fields = ["name"]


admin.site.register(Book, BookAdmin)
admin.site.register(Author, AuthorAdmin)
