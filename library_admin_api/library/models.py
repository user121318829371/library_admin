from django.contrib.auth.models import User
from django.db import models


class Author(models.Model):
    """作者表"""

    name = models.CharField(max_length=30, db_index=True, verbose_name='作者姓名')
    country = models.CharField(max_length=20, blank=True, default='', verbose_name='国籍')
    birth_year = models.SmallIntegerField(null=True, blank=True, verbose_name='出生年份')
    masterpiece = models.CharField(max_length=50, blank=True, default='', verbose_name='代表作')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        db_table = 'author'
        verbose_name = '作者'
        verbose_name_plural = '作者'

    def __str__(self):
        return self.name


class Publisher(models.Model):
    """出版社表"""

    name = models.CharField(max_length=50, unique=True, verbose_name='出版社名称')
    city = models.CharField(max_length=20, blank=True, default='', verbose_name='所在城市')
    founded_year = models.SmallIntegerField(null=True, blank=True, verbose_name='成立年份')
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='联系电话')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        db_table = 'publisher'
        verbose_name = '出版社'
        verbose_name_plural = '出版社'

    def __str__(self):
        return self.name


class Category(models.Model):
    """图书分类表"""

    name = models.CharField(max_length=20, unique=True, verbose_name='分类名称')
    sort_order = models.IntegerField(default=0, verbose_name='排序值')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'category'
        ordering = ['sort_order', 'id']
        verbose_name = '图书分类'
        verbose_name_plural = '图书分类'

    def __str__(self):
        return self.name


class Book(models.Model):
    """图书表"""

    title = models.CharField(max_length=100, db_index=True, verbose_name='书名')
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name='books',
        verbose_name='作者',
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name='books',
        verbose_name='出版社',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name='分类',
    )
    isbn = models.CharField(max_length=13, unique=True, verbose_name='ISBN号')
    publish_date = models.DateField(verbose_name='出版日期')
    stock = models.IntegerField(default=0, verbose_name='库存数量')
    cover_color = models.CharField(max_length=7, default='#4F6BFF', verbose_name='封面色值')
    cover_image = models.TextField(blank=True, default='', verbose_name='封面图片（Base64 Data URL）')
    intro = models.TextField(blank=True, default='', verbose_name='图书简介')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='入库时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        db_table = 'book'
        verbose_name = '图书'
        verbose_name_plural = '图书'
        constraints = [
            models.CheckConstraint(condition=models.Q(stock__gte=0), name='book_stock_gte_0'),
        ]

    def __str__(self):
        return self.title


class BorrowRecord(models.Model):
    """借阅记录表"""

    STATUS_BORROWING = '借阅中'
    STATUS_RETURNED = '已归还'
    STATUS_CHOICES = [
        (STATUS_BORROWING, '借阅中'),
        (STATUS_RETURNED, '已归还'),
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name='borrows',
        verbose_name='借阅图书',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='borrows',
        verbose_name='借阅人',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_BORROWING,
        verbose_name='借阅状态',
    )
    borrowed_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='借出时间')
    returned_at = models.DateTimeField(null=True, blank=True, verbose_name='归还时间')

    class Meta:
        db_table = 'borrow_record'
        ordering = ['-borrowed_at', '-id']
        verbose_name = '借阅记录'
        verbose_name_plural = '借阅记录'
        constraints = [
            # 同一用户对同一本书只能有一条「借阅中」记录（数据库层兜底，防止并发重复借阅）
            models.UniqueConstraint(
                fields=['book', 'user'],
                condition=models.Q(status='借阅中'),
                name='uniq_borrowing_book_user',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.book.title} - {self.status}'
