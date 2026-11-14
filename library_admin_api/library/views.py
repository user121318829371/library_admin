import secrets
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Author, Book, BorrowRecord, Category, Publisher
from .serializers import author_dict, book_dict, borrow_dict, publisher_dict


ADMIN_DENIED = '不是管理员，无法操作'


class _OutOfStock(Exception):
    """借阅时库存已被并发请求扣完"""


class _StockConflict(Exception):
    """调整库存时与并发操作冲突"""


# ---------- 统一响应 ----------

def ok(data=None, message='success'):
    return Response({'code': 0, 'message': message, 'data': data})


def fail(message, code=1):
    return Response({'code': code, 'message': message, 'data': None})


# ---------- 权限辅助 ----------

def _is_admin(user):
    """图书管理员：超级用户，或用户名为 admin"""
    return bool(user and user.is_authenticated and (user.is_superuser or user.username == 'admin'))


def _require_login(request):
    """返回当前登录用户；未登录时返回 (None, 错误响应)"""
    if not request.user or not request.user.is_authenticated:
        return None, fail('请先登录')
    return request.user, None


def _require_admin(request):
    """返回当前管理员用户；非管理员时返回 (None, 错误响应)"""
    user, err = _require_login(request)
    if err:
        return None, err
    if not _is_admin(user):
        return None, fail(ADMIN_DENIED)
    return user, None


def paginate(queryset, request, to_dict):
    """通用分页：page / pageSize 查询参数，返回 {list,total,page,pageSize}"""
    try:
        page = max(int(request.query_params.get('page', 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = max(int(request.query_params.get('pageSize', 10)), 1)
    except (TypeError, ValueError):
        page_size = 10
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    return ok({
        'list': [to_dict(obj) for obj in page_obj.object_list],
        'total': paginator.count,
        'page': page_obj.number,
        'pageSize': page_size,
    })


# ---------- 认证 ----------

@api_view(['POST'])
def login(request):
    """登录：校验用户名密码，成功返回 token。"""
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    if not username or not password:
        return fail('请输入账号和密码')

    user = authenticate(request, username=username, password=password)
    if user is None:
        return fail('账号或密码错误')

    try:
        token, _ = Token.objects.get_or_create(user=user)
    except IntegrityError:
        # 并发登录可能同时创建 Token，唯一约束冲突后直接读取已有记录
        token = Token.objects.get(user=user)
    return ok({
        'token': token.key,
        'user': {'name': user.username},
        'isAdmin': _is_admin(user),
    })


@api_view(['POST'])
def register(request):
    """注册：最简单的用户名 + 密码，写入 Django 内置 auth_user 表。"""
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    if not username or not password:
        return fail('请输入账号和密码')
    if len(username) > 150:
        return fail('用户名过长（最多 150 字符）')
    if len(password) < 6:
        return fail('密码至少 6 位')
    if User.objects.filter(username=username).exists():
        return fail('该用户名已被注册')

    try:
        user = User.objects.create_user(username=username, password=password)
    except IntegrityError:
        # 并发注册同名账号时由 auth_user.username 唯一约束兜底
        return fail('该用户名已被注册')
    return ok({'id': user.id, 'username': user.username, 'isAdmin': False}, '注册成功')


# ---------- 字典 / 选项 ----------

@api_view(['GET'])
def categories(request):
    return ok(list(Category.objects.values_list('name', flat=True)))


@api_view(['GET'])
def countries(request):
    rows = Author.objects.exclude(country='').values_list('country', flat=True)
    return ok(sorted(set(rows)))


@api_view(['GET'])
def cities(request):
    rows = Publisher.objects.exclude(city='').values_list('city', flat=True)
    return ok(sorted(set(rows)))


@api_view(['GET'])
def author_options(request):
    keyword = request.query_params.get('keyword', '').strip()
    qs = Author.objects.order_by('id')
    if keyword:
        qs = qs.filter(name__icontains=keyword)
    return ok([{'id': a.id, 'name': a.name} for a in qs[:20]])


@api_view(['GET'])
def publisher_options(request):
    keyword = request.query_params.get('keyword', '').strip()
    qs = Publisher.objects.order_by('id')
    if keyword:
        qs = qs.filter(name__icontains=keyword)
    return ok([{'id': p.id, 'name': p.name} for p in qs[:20]])


# ---------- 图书 ----------

def _get_category_id(payload):
    """前端传分类名称，这里转换为 category_id"""
    name = payload.get('category')
    if not name:
        return None
    category = Category.objects.filter(name=name).first()
    if category is None:
        raise ValueError(f'分类「{name}」不存在')
    return category.id


def _check_fk(payload, field, model, label):
    value = payload.get(field)
    if value in (None, ''):
        raise ValueError(f'请选择{label}')
    if not model.objects.filter(pk=value).exists():
        raise ValueError(f'{label}不存在')
    return value


@api_view(['GET', 'POST'])
def book_list(request):
    if request.method == 'GET':
        qs = Book.objects.select_related('author', 'publisher', 'category')
        keyword = request.query_params.get('keyword', '').strip()
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(isbn__icontains=keyword))
        author_id = request.query_params.get('authorId')
        if author_id:
            qs = qs.filter(author_id=author_id)
        publisher_id = request.query_params.get('publisherId')
        if publisher_id:
            qs = qs.filter(publisher_id=publisher_id)
        category = request.query_params.get('category', '').strip()
        if category:
            qs = qs.filter(category__name=category)
        date_start = request.query_params.get('dateStart')
        date_end = request.query_params.get('dateEnd')
        if date_start and date_end:
            qs = qs.filter(publish_date__gte=date_start, publish_date__lte=date_end)
        qs = qs.order_by('-created_at', '-id')
        return paginate(qs, request, book_dict)

    # POST 新增
    _, err = _require_admin(request)
    if err:
        return err
    p = request.data
    try:
        author_id = _check_fk(p, 'authorId', Author, '作者')
        publisher_id = _check_fk(p, 'publisherId', Publisher, '出版社')
        category_id = _get_category_id(p)
    except ValueError as e:
        return fail(str(e))
    if not (p.get('title') or '').strip():
        return fail('书名不能为空')
    if not (p.get('isbn') or '').strip():
        return fail('ISBN 不能为空')

    cover_colors = ['#4F6BFF', '#22C55E', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#84CC16']
    title = p['title'].strip()
    try:
        book = Book.objects.create(
            title=title,
            author_id=author_id,
            publisher_id=publisher_id,
            category_id=category_id,
            isbn=p['isbn'].strip(),
            publish_date=p.get('publishDate') or timezone.now().date(),
            stock=p.get('stock') or 0,
            intro=p.get('intro') or '',
            cover_color=cover_colors[ord(title[0]) % len(cover_colors)],
            cover_image=p.get('coverImage') or '',
        )
    except IntegrityError:
        return fail('ISBN 已存在，请勿重复入库')
    book.refresh_from_db()
    return ok(book_dict(book), '新增成功')


@api_view(['PUT', 'DELETE'])
def book_detail(request, pk):
    _, err = _require_admin(request)
    if err:
        return err
    book = Book.objects.select_related('author', 'publisher', 'category').filter(pk=pk).first()
    if book is None:
        return fail('图书不存在')

    if request.method == 'DELETE':
        try:
            book.delete()
        except ProtectedError:
            return fail(f'该图书存在 {book.borrows.count()} 条借阅记录，无法删除')
        return ok(None, '删除成功')

    # PUT 更新
    p = request.data
    try:
        book.author_id = _check_fk(p, 'authorId', Author, '作者')
        book.publisher_id = _check_fk(p, 'publisherId', Publisher, '出版社')
        book.category_id = _get_category_id(p)
    except ValueError as e:
        return fail(str(e))
    book.title = (p.get('title') or book.title).strip()
    book.publish_date = p.get('publishDate') or book.publish_date
    book.intro = p.get('intro') if p.get('intro') is not None else book.intro
    if p.get('coverImage') is not None:
        book.cover_image = p['coverImage'] or ''
    new_isbn = (p.get('isbn') or '').strip()
    if new_isbn:
        book.isbn = new_isbn

    # 库存按「增量」更新：先算出本次调整量，再用 F() 原子加减，
    # 避免编辑表单覆盖并发借阅/归还造成的库存变化
    delta = None
    if p.get('stock') is not None:
        try:
            new_stock = int(p.get('stock'))
        except (TypeError, ValueError):
            return fail('库存必须为整数')
        if new_stock < 0:
            return fail('库存不能小于 0')
        delta = new_stock - book.stock

    try:
        with transaction.atomic():
            book.save(update_fields=[
                'title', 'author', 'publisher', 'category',
                'publish_date', 'intro', 'cover_image', 'isbn', 'updated_at',
            ])
            if delta:
                qs = Book.objects.filter(pk=pk)
                if delta < 0:
                    qs = qs.filter(stock__gte=-delta)
                if not qs.update(stock=F('stock') + delta):
                    raise _StockConflict()
    except _StockConflict:
        return fail('库存已被其他操作修改，请刷新后重试')
    except IntegrityError:
        return fail('ISBN 已存在')
    book.refresh_from_db()
    return ok(book_dict(book), '保存成功')


# ---------- 作者 ----------

@api_view(['GET', 'POST'])
def author_list(request):
    if request.method == 'GET':
        qs = Author.objects.annotate(works_count=Count('books'))
        keyword = request.query_params.get('keyword', '').strip()
        if keyword:
            qs = qs.filter(name__icontains=keyword)
        country = request.query_params.get('country', '').strip()
        if country:
            qs = qs.filter(country=country)
        qs = qs.order_by('-created_at', '-id')
        return paginate(qs, request, lambda a: author_dict(a, a.works_count))

    _, err = _require_admin(request)
    if err:
        return err
    p = request.data
    if not (p.get('name') or '').strip():
        return fail('作者姓名不能为空')
    author = Author.objects.create(
        name=p['name'].strip(),
        country=p.get('country') or '',
        birth_year=p.get('birthYear') or None,
        masterpiece=p.get('masterpiece') or '',
    )
    return ok(author_dict(author, 0), '新增成功')


@api_view(['PUT', 'DELETE'])
def author_detail(request, pk):
    _, err = _require_admin(request)
    if err:
        return err
    author = Author.objects.filter(pk=pk).first()
    if author is None:
        return fail('作者不存在')

    if request.method == 'DELETE':
        try:
            author.delete()
        except ProtectedError:
            return fail(f'该作者名下存在 {author.books.count()} 本图书，无法删除')
        return ok(None, '删除成功')

    p = request.data
    author.name = (p.get('name') or author.name).strip()
    author.country = p.get('country') or ''
    author.birth_year = p.get('birthYear') or None
    author.masterpiece = p.get('masterpiece') or ''
    author.save()
    return ok(author_dict(author), '保存成功')


# ---------- 出版社 ----------

@api_view(['GET', 'POST'])
def publisher_list(request):
    if request.method == 'GET':
        qs = Publisher.objects.annotate(book_count=Count('books'))
        keyword = request.query_params.get('keyword', '').strip()
        if keyword:
            qs = qs.filter(name__icontains=keyword)
        city = request.query_params.get('city', '').strip()
        if city:
            qs = qs.filter(city=city)
        qs = qs.order_by('-created_at', '-id')
        return paginate(qs, request, lambda p: publisher_dict(p, p.book_count))

    _, err = _require_admin(request)
    if err:
        return err
    p = request.data
    if not (p.get('name') or '').strip():
        return fail('出版社名称不能为空')
    try:
        publisher = Publisher.objects.create(
            name=p['name'].strip(),
            city=p.get('city') or '',
            founded_year=p.get('foundedYear') or None,
            phone=p.get('phone') or '',
        )
    except IntegrityError:
        return fail('该出版社已存在')
    return ok(publisher_dict(publisher, 0), '新增成功')


@api_view(['PUT', 'DELETE'])
def publisher_detail(request, pk):
    _, err = _require_admin(request)
    if err:
        return err
    publisher = Publisher.objects.filter(pk=pk).first()
    if publisher is None:
        return fail('出版社不存在')

    if request.method == 'DELETE':
        try:
            publisher.delete()
        except ProtectedError:
            return fail(f'该出版社名下存在 {publisher.books.count()} 本图书，无法删除')
        return ok(None, '删除成功')

    p = request.data
    publisher.name = (p.get('name') or publisher.name).strip()
    publisher.city = p.get('city') or ''
    publisher.founded_year = p.get('foundedYear') or None
    publisher.phone = p.get('phone') or ''
    try:
        publisher.save()
    except IntegrityError:
        return fail('该出版社已存在')
    return ok(publisher_dict(publisher), '保存成功')


# ---------- 借阅 ----------

@api_view(['POST'])
def borrow_book(request, pk):
    """借阅图书：库存 -1，生成一条『借阅中』记录"""
    user, err = _require_login(request)
    if err:
        return err

    book = Book.objects.filter(pk=pk).first()
    if book is None:
        return fail('图书不存在')
    if book.stock <= 0:
        return fail('该图书已无库存，无法借阅')
    # 提前给出友好提示；并发重复借阅由数据库唯一约束兜底
    if BorrowRecord.objects.filter(
        book_id=pk, user=user, status=BorrowRecord.STATUS_BORROWING
    ).exists():
        return fail('你已借阅该图书且尚未归还')

    try:
        with transaction.atomic():
            # 条件更新 + F() 原子扣减：库存为 0 时不会命中，避免并发超借
            if not Book.objects.filter(pk=pk, stock__gte=1).update(stock=F('stock') - 1):
                raise _OutOfStock()
            record = BorrowRecord.objects.create(book_id=pk, user=user)
    except _OutOfStock:
        return fail('该图书已无库存，无法借阅')
    except IntegrityError:
        # 并发提交触发 uniq_borrowing_book_user 约束，事务已回滚（库存不会被多扣）
        return fail('你已借阅该图书且尚未归还')

    book.refresh_from_db()
    return ok(borrow_dict(record, with_stock=True), '借阅成功')


@api_view(['GET'])
def borrow_list(request):
    """借阅历史列表（全部用户可见）"""
    qs = BorrowRecord.objects.select_related('book', 'user')
    keyword = request.query_params.get('keyword', '').strip()
    if keyword:
        qs = qs.filter(Q(book__title__icontains=keyword) | Q(user__username__icontains=keyword))
    status_val = request.query_params.get('status', '').strip()
    if status_val:
        qs = qs.filter(status=status_val)
    qs = qs.order_by('-borrowed_at', '-id')
    return paginate(qs, request, borrow_dict)


@api_view(['POST'])
def borrow_return(request, pk):
    """归还图书（仅管理员）：记录置为已归还，库存 +1"""
    _, err = _require_admin(request)
    if err:
        return err

    record = BorrowRecord.objects.select_related('book', 'user').filter(pk=pk).first()
    if record is None:
        return fail('借阅记录不存在')

    with transaction.atomic():
        # 仅当记录仍是「借阅中」时才更新：并发重复归还只有一次会命中，避免库存多加
        if not BorrowRecord.objects.filter(
            pk=pk, status=BorrowRecord.STATUS_BORROWING
        ).update(status=BorrowRecord.STATUS_RETURNED, returned_at=timezone.now()):
            return fail('该借阅记录已归还')
        Book.objects.filter(pk=record.book_id).update(stock=F('stock') + 1)

    record.refresh_from_db()
    record.book.refresh_from_db()
    return ok(borrow_dict(record, with_stock=True), '归还成功')


# ---------- Dashboard ----------

def _trend_calc(dates, month_keys):
    """本月新增环比上月新增的百分比"""
    cur = sum(1 for d in dates if d.strftime('%Y-%m') == month_keys[-1])
    prev = sum(1 for d in dates if d.strftime('%Y-%m') == month_keys[-2])
    if prev == 0:
        return 100 if cur > 0 else 0
    return round((cur - prev) / prev * 100)


@api_view(['GET'])
def dashboard(request):
    now = timezone.now()

    # 近 12 个月月份键
    month_keys = []
    y, m = now.year, now.month
    for _ in range(12):
        month_keys.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    month_keys.reverse()
    month_strs = [f'{y}-{m:02d}' for y, m in month_keys]

    books = Book.objects.select_related('author', 'publisher', 'category')
    book_dates = list(books.values_list('created_at', flat=True))
    author_dates = list(Author.objects.values_list('created_at', flat=True))
    publisher_dates = list(Publisher.objects.values_list('created_at', flat=True))

    today = now.date()
    yesterday = today - timedelta(days=1)
    today_count = sum(1 for d in book_dates if d.date() == today)
    yesterday_count = sum(1 for d in book_dates if d.date() == yesterday)
    if yesterday_count == 0:
        today_trend = 100 if today_count > 0 else 0
    else:
        today_trend = round((today_count - yesterday_count) / yesterday_count * 100)

    summary = {
        'bookCount': books.count(),
        'authorCount': Author.objects.count(),
        'publisherCount': Publisher.objects.count(),
        'todayCount': today_count,
        'bookTrend': _trend_calc(book_dates, month_strs),
        'authorTrend': _trend_calc(author_dates, month_strs),
        'publisherTrend': _trend_calc(publisher_dates, month_strs),
        'todayTrend': today_trend,
    }

    trend = [
        {'month': ms[2:], 'count': sum(1 for d in book_dates if d.strftime('%Y-%m') == ms)}
        for ms in month_strs
    ]

    category_dist = [
        {'name': row['category__name'], 'value': row['value']}
        for row in books.values('category__name')
        .annotate(value=Count('id'))
        .filter(value__gt=0, category__name__isnull=False)
        .order_by('-value')
    ]

    top_publishers = [
        {'name': row['name'], 'value': row['value']}
        for row in Publisher.objects.annotate(value=Count('books'))
        .filter(value__gt=0)
        .order_by('-value')
        .values('name', 'value')[:6]
    ]

    latest = [book_dict(b) for b in books.order_by('-created_at', '-id')[:6]]

    return ok({
        'summary': summary,
        'trend': trend,
        'categoryDist': category_dist,
        'topPublishers': top_publishers,
        'latest': latest,
    })
