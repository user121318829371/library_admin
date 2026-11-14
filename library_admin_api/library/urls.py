from django.urls import path

from . import views

urlpatterns = [
    # 认证
    path('auth/login', views.login),
    path('auth/register', views.register),
    # 字典 / 选项
    path('dict/categories', views.categories),
    path('dict/countries', views.countries),
    path('dict/cities', views.cities),
    path('options/authors', views.author_options),
    path('options/publishers', views.publisher_options),
    # 图书 / 作者 / 出版社 CRUD
    path('books', views.book_list),
    path('books/<int:pk>', views.book_detail),
    path('authors', views.author_list),
    path('authors/<int:pk>', views.author_detail),
    path('publishers', views.publisher_list),
    path('publishers/<int:pk>', views.publisher_detail),
    # 借阅
    path('books/<int:pk>/borrow', views.borrow_book),
    path('borrows', views.borrow_list),
    path('borrows/<int:pk>/return', views.borrow_return),
    # Dashboard 聚合
    path('dashboard', views.dashboard),
]
