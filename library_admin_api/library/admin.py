from django.contrib import admin

from .models import Author, Book, Category, Publisher


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country', 'birth_year', 'masterpiece', 'created_at')
    search_fields = ('name',)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city', 'founded_year', 'phone', 'created_at')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sort_order')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'publisher', 'category', 'isbn', 'stock', 'publish_date', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'isbn')
