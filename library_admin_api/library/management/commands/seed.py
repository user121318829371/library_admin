"""种子数据：与前端 Mock 层（src/api/mock.js）的种子完全一致。

用法：python manage.py seed
- 幂等：已存在数据时先清空业务表再播种。
- 由于 models 的 created_at 使用 auto_now_add，创建后再用 update() 写回演示用时间。
"""
import os
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from library.models import Author, Book, Category, Publisher

CATEGORIES = ['文学', '科技', '历史', '艺术', '经济', '教育']
COVER_COLORS = ['#4F6BFF', '#22C55E', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#84CC16']

AUTHORS_SEED = [
    {'name': '路遥', 'country': '中国', 'birth_year': 1949, 'masterpiece': '平凡的世界'},
    {'name': '余华', 'country': '中国', 'birth_year': 1960, 'masterpiece': '活着'},
    {'name': '莫言', 'country': '中国', 'birth_year': 1955, 'masterpiece': '红高粱家族'},
    {'name': '刘慈欣', 'country': '中国', 'birth_year': 1963, 'masterpiece': '三体'},
    {'name': '村上春树', 'country': '日本', 'birth_year': 1949, 'masterpiece': '挪威的森林'},
    {'name': '东野圭吾', 'country': '日本', 'birth_year': 1958, 'masterpiece': '白夜行'},
    {'name': '加西亚·马尔克斯', 'country': '哥伦比亚', 'birth_year': 1927, 'masterpiece': '百年孤独'},
    {'name': 'J.K.罗琳', 'country': '英国', 'birth_year': 1965, 'masterpiece': '哈利·波特与魔法石'},
    {'name': '乔治·奥威尔', 'country': '英国', 'birth_year': 1903, 'masterpiece': '1984'},
    {'name': '海明威', 'country': '美国', 'birth_year': 1899, 'masterpiece': '老人与海'},
    {'name': '凯文·凯利', 'country': '美国', 'birth_year': 1952, 'masterpiece': '失控'},
    {'name': '吴军', 'country': '美国', 'birth_year': 1967, 'masterpiece': '浪潮之巅'},
    {'name': '当年明月', 'country': '中国', 'birth_year': 1979, 'masterpiece': '明朝那些事儿'},
    {'name': '贡布里希', 'country': '英国', 'birth_year': 1909, 'masterpiece': '艺术的故事'},
    {'name': '曼昆', 'country': '美国', 'birth_year': 1958, 'masterpiece': '经济学原理'},
    {'name': '钱钟书', 'country': '中国', 'birth_year': 1910, 'masterpiece': '围城'},
]

PUBLISHERS_SEED = [
    {'name': '人民文学出版社', 'city': '北京', 'founded_year': 1951, 'phone': '010-65288961'},
    {'name': '中信出版社', 'city': '北京', 'founded_year': 1988, 'phone': '010-84849055'},
    {'name': '机械工业出版社', 'city': '北京', 'founded_year': 1952, 'phone': '010-88379639'},
    {'name': '电子工业出版社', 'city': '北京', 'founded_year': 1982, 'phone': '010-88254000'},
    {'name': '上海译文出版社', 'city': '上海', 'founded_year': 1978, 'phone': '021-62460100'},
    {'name': '译林出版社', 'city': '南京', 'founded_year': 1988, 'phone': '025-83302800'},
    {'name': '南海出版公司', 'city': '海口', 'founded_year': 1988, 'phone': '0898-65350227'},
    {'name': '重庆出版社', 'city': '重庆', 'founded_year': 1950, 'phone': '023-68809799'},
]

# [书名, 作者索引, 分类]
BOOKS_SEED = [
    ['平凡的世界', 0, '文学'], ['人生', 0, '文学'],
    ['活着', 1, '文学'], ['许三观卖血记', 1, '文学'], ['兄弟', 1, '文学'], ['文城', 1, '文学'],
    ['红高粱家族', 2, '文学'], ['蛙', 2, '文学'], ['丰乳肥臀', 2, '文学'],
    ['三体', 3, '文学'], ['流浪地球', 3, '文学'], ['球状闪电', 3, '文学'],
    ['挪威的森林', 4, '文学'], ['海边的卡夫卡', 4, '文学'], ['1Q84', 4, '文学'],
    ['白夜行', 5, '文学'], ['嫌疑人X的献身', 5, '文学'], ['解忧杂货店', 5, '文学'], ['恶意', 5, '文学'],
    ['百年孤独', 6, '文学'], ['霍乱时期的爱情', 6, '文学'],
    ['哈利·波特与魔法石', 7, '文学'], ['哈利·波特与密室', 7, '文学'],
    ['1984', 8, '文学'], ['动物农场', 8, '文学'],
    ['老人与海', 9, '文学'], ['永别了，武器', 9, '文学'],
    ['失控', 10, '科技'], ['必然', 10, '科技'],
    ['浪潮之巅', 11, '科技'], ['数学之美', 11, '教育'], ['智能时代', 11, '科技'], ['大学之路', 11, '教育'],
    ['明朝那些事儿（壹）', 12, '历史'], ['明朝那些事儿（贰）', 12, '历史'],
    ['艺术的故事', 13, '艺术'], ['秩序感', 13, '艺术'],
    ['经济学原理：微观经济学分册', 14, '经济'], ['经济学原理：宏观经济学分册', 14, '经济'],
    ['围城', 15, '文学'], ['管锥编', 15, '文学'],
]


def shift_month(year, month, offset):
    """year-month 向前推 offset 个月"""
    total = year * 12 + (month - 1) - offset
    return total // 12, total % 12 + 1


class Command(BaseCommand):
    help = '清空并重建演示种子数据（分类/作者/出版社/图书 + admin 账号）'

    def handle(self, *args, **options):
        now = datetime.now()

        Book.objects.all().delete()
        Author.objects.all().delete()
        Publisher.objects.all().delete()
        Category.objects.all().delete()

        # 分类
        for i, name in enumerate(CATEGORIES):
            Category.objects.create(name=name, sort_order=i)
        category_map = {c.name: c.id for c in Category.objects.all()}

        # 作者
        authors = []
        for i, a in enumerate(AUTHORS_SEED):
            authors.append(Author.objects.create(**a))
        for i, a in enumerate(authors):
            y, m = shift_month(now.year, now.month, i % 12)
            Author.objects.filter(pk=a.pk).update(
                created_at=datetime(y, m, (i * 7) % 27 + 1, 9 + (i % 8), (i * 13) % 60)
            )

        # 出版社
        publishers = []
        for p in PUBLISHERS_SEED:
            publishers.append(Publisher.objects.create(**p))
        for i, p in enumerate(publishers):
            y, m = shift_month(now.year, now.month, (i * 2) % 12)
            Publisher.objects.filter(pk=p.pk).update(
                created_at=datetime(y, m, (i * 11) % 27 + 1, 10, 0)
            )

        # 图书
        for i, (title, ai, category) in enumerate(BOOKS_SEED):
            author = authors[ai]
            book = Book.objects.create(
                title=title,
                author=author,
                publisher=publishers[i % len(publishers)],
                category_id=category_map[category],
                isbn=f'9787{100000000 + i * 137}',
                publish_date=f'{2000 + (i * 5) % 25}-{(i * 3) % 12 + 1:02d}-{(i * 7) % 28 + 1:02d}',
                stock=(i * 7) % 23,
                intro=f'《{title}》是{author.name}的代表作品之一，馆藏热门图书。',
                cover_color=COVER_COLORS[i % len(COVER_COLORS)],
            )
            # 入库时间统一为当天（按序号递增），保证「最新入库」不早于当天
            created = datetime(now.year, now.month, now.day, 8 + i // 6, (i * 3) % 60)
            Book.objects.filter(pk=book.pk).update(created_at=created)

        # 管理员账号（admin），供 Django Admin 与登录接口使用
        # 密码从环境变量 DJANGO_ADMIN_PASSWORD 读取：运行前请填入你的管理员初始密码
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                'admin',
                'admin@example.com',
                os.environ.get('DJANGO_ADMIN_PASSWORD', '填入你的管理员初始密码'),
            )

        self.stdout.write(self.style.SUCCESS(
            f'种子完成：分类 {Category.objects.count()}，作者 {Author.objects.count()}，'
            f'出版社 {Publisher.objects.count()}，图书 {Book.objects.count()}，'
            f'管理员 admin'
        ))
