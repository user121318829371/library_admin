"""模型 → 前端 camelCase 字典的序列化函数。

前端字段命名沿用开发文档约定（camelCase），
因此这里不用 DRF Serializer，直接手写转换，保持输出形状与 Mock 层一致。
"""

COVER_COLORS = ['#4F6BFF', '#22C55E', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#84CC16']


def fmt_dt(dt):
    """DateTime → 'YYYY-MM-DD HH:mm'（与 Mock 层 fmtDateTime 一致）"""
    return dt.strftime('%Y-%m-%d %H:%M') if dt else None


def fmt_d(d):
    """Date → 'YYYY-MM-DD'"""
    return d.strftime('%Y-%m-%d') if d else None


def avatar_color(name):
    """按姓名首字符分配头像色（与 Mock 层一致）"""
    return COVER_COLORS[ord(name[0]) % len(COVER_COLORS)] if name else COVER_COLORS[0]


def book_dict(b):
    return {
        'id': b.id,
        'title': b.title,
        'authorId': b.author_id,
        'publisherId': b.publisher_id,
        'isbn': b.isbn,
        'category': b.category.name if b.category else '',
        'publishDate': fmt_d(b.publish_date),
        'stock': b.stock,
        'intro': b.intro,
        'cover': {'color': b.cover_color, 'image': b.cover_image or ''},
        'createdAt': fmt_dt(b.created_at),
        'authorName': b.author.name if b.author_id else '-',
        'publisherName': b.publisher.name if b.publisher_id else '-',
    }


def author_dict(a, works_count=None):
    return {
        'id': a.id,
        'name': a.name,
        'country': a.country,
        'birthYear': a.birth_year,
        'masterpiece': a.masterpiece,
        'createdAt': fmt_dt(a.created_at),
        'worksCount': works_count if works_count is not None else a.books.count(),
        'color': avatar_color(a.name),
    }


def publisher_dict(p, book_count=None):
    return {
        'id': p.id,
        'name': p.name,
        'city': p.city,
        'foundedYear': p.founded_year,
        'phone': p.phone,
        'createdAt': fmt_dt(p.created_at),
        'bookCount': book_count if book_count is not None else p.books.count(),
    }


def borrow_dict(rec, with_stock=False):
    data = {
        'id': rec.id,
        'bookId': rec.book_id,
        'bookTitle': rec.book.title if rec.book_id else '-',
        'bookIsbn': rec.book.isbn if rec.book_id else '',
        'userId': rec.user_id,
        'userName': rec.user.username if rec.user_id else '-',
        'status': rec.status,
        'borrowedAt': fmt_dt(rec.borrowed_at),
        'returnedAt': fmt_dt(rec.returned_at),
    }
    if with_stock:
        data['stock'] = rec.book.stock
    return data
