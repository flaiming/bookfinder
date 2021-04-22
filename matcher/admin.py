from django.contrib import admin
from matcher.models import Book, BookCover, Author, BookImport


class BookCoverInline(admin.TabularInline):
    model = BookCover
    readonly_fields = ["profile"]
    extra = 0


class BookAdmin(admin.ModelAdmin):
    readonly_fields = ["authors"]
    search_fields = ["name"]
    inlines = [BookCoverInline]


class AuthorAdmin(admin.ModelAdmin):
    search_fields = ["name"]


admin.site.register(Book, BookAdmin)
admin.site.register(Author, AuthorAdmin)


class BookImportAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name", "active", "price_type"]


admin.site.register(BookImport, BookImportAdmin)
