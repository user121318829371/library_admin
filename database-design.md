# 图书管理系统 · 数据库设计文档

> 版本：v1.1（新增借阅记录表 `borrow_record`，支撑图书借阅与权限控制）
> 数据库：SQLite 3（Django 框架内置默认数据库）
> ORM：Django ORM（Django 4.x / 5.x）
> 配套前端文档：《图书管理系统-前端开发文档.md》

---

## 目录

1. [设计概述](#1-设计概述)
2. [ER 关系图](#2-er-关系图)
3. [数据表详细设计](#3-数据表详细设计)
4. [索引设计](#4-索引设计)
5. [Django models.py 参考实现](#5-django-modelspy-参考实现)
6. [种子数据说明](#6-种子数据说明)
7. [前端页面与数据表字段映射](#7-前端页面与数据表字段映射)
8. [Dashboard 统计 SQL 实现参考](#8-dashboard-统计-sql-实现参考)
9. [SQLite 注意事项与后续迁移建议](#9-sqlite-注意事项与后续迁移建议)
10. [预留扩展](#10-预留扩展)

---

## 1. 设计概述

### 1.1 设计依据

本设计来源于前端原型 Mock 数据层（`src/api/mock.js`）中使用的全部页面数据，覆盖以下功能页面：

| 页面 | 涉及数据 |
| --- | --- |
| 登录页 | 用户账号、密码 |
| 数据大屏 | 图书/作者/出版社总数、今日入库、近 12 个月入库趋势、分类分布、Top 出版社、最新入库 |
| 图书管理 | 图书的增删改查、搜索、分页、多条件过滤、详情 |
| 作者管理 | 作者的增删改查、搜索、国籍过滤、作品数量统计、删除保护 |
| 出版社管理 | 出版社的增删改查、搜索、城市过滤、出版物数量统计、删除保护 |

### 1.2 命名规范

- 表名：小写下划线，单数形式（如 `book`、`author`）。
- 字段名：小写下划线（如 `publish_date`、`created_at`）。
- 所有业务表统一包含 `created_at` / `updated_at` 审计字段。
- 主键统一为自增整数 `id`（Django `BigAutoField`）。

### 1.3 字符集与时间

- SQLite 默认 UTF-8 编码，直接支持中文存储。
- SQLite 无原生日期/时间类型，Django 将 `DateField` / `DateTimeField` 以 ISO 8601 文本（`YYYY-MM-DD` / `YYYY-MM-DD HH:MM:SS.ffffff`）存储，比较与排序行为正常。
- 时间统一使用北京时间（`settings.TIME_ZONE = 'Asia/Shanghai'`，`USE_TZ = True` 时 Django 内部以 UTC 存储，展示层转换）。

---

## 2. ER 关系图

```
┌──────────────┐         ┌──────────────────┐         ┌────────────────┐
│   author     │         │       book        │         │   publisher    │
│   作者表      │ 1     N │      图书表        │ N     1 │    出版社表     │
│──────────────│─────────│──────────────────│─────────│────────────────│
│ id (PK)      │◄────────│ author_id (FK)    │         │ id (PK)        │
│ name         │         │ publisher_id (FK) ├────────►│ name (UNIQUE)  │
│ country      │         │ category_id (FK)  │         │ city           │
│ birth_year   │         │ title             │         │ founded_year   │
│ masterpiece  │         │ isbn (UNIQUE)     │         │ phone          │
│ created_at   │         │ publish_date      │         │ created_at     │
│ updated_at   │         │ stock             │         │ updated_at     │
└──────────────┘         │ cover_color       │         └────────────────┘
                         │ intro             │
┌──────────────┐         │ created_at        │         ┌────────────────┐
│  category    │ 1     N │ updated_at        │         │   auth_user    │
│   分类表      │◄────────│                   │         │ (Django 内置)   │
│──────────────│         └──────────────────┘         │────────────────│
│ id (PK)      │                                      │ id (PK)        │
│ name (UNIQUE)│                                      │ username       │
│ sort_order   │                                      │ password(哈希)  │
│ created_at   │                                      │ ...            │
└──────────────┘                                      └────────────────┘

        ┌──────────────────┐        ┌──────────────────┐
        │      book        │ 1    N │  borrow_record   │
        │      图书表       │───────│    借阅记录表      │
        └──────────────────┘        │──────────────────│
                                    │ id (PK)          │
        ┌──────────────────┐        │ book_id (FK)     │
        │    auth_user     │ 1    N │ user_id (FK)     │
        │  (Django 内置)    │───────│ status           │
        └──────────────────┘        │ borrowed_at      │
                                    │ returned_at      │
                                    └──────────────────┘
```

**关系说明：**

| 关系 | 基数 | 删除策略 | 说明 |
| --- | --- | --- | --- |
| 作者 — 图书 | 1 : N | `PROTECT`（保护） | 作者名下存在图书时禁止删除（对应前端删除保护提示） |
| 出版社 — 图书 | 1 : N | `PROTECT`（保护） | 出版社名下存在图书时禁止删除 |
| 分类 — 图书 | 1 : N | `SET_NULL`（置空） | 分类被删除时，图书分类置为空，图书保留 |
| 图书 — 借阅记录 | 1 : N | `PROTECT`（保护） | 图书存在借阅记录时禁止删除，避免历史记录悬空 |
| 用户 — 借阅记录 | 1 : N | `CASCADE`（级联） | 用户注销时其借阅记录一并删除 |
| 权限角色 | 独立 | — | 由 `auth_user.is_superuser`（或 `username='admin'`）判定：管理员可增删改，普通用户仅可借阅 |

---

## 3. 数据表详细设计

### 3.1 作者表 `author`

存储作者基本信息，对应"作者管理"页面。

| 字段名 | Django 字段类型 | SQLite 类型 | 约束 | 中文注释 |
| --- | --- | --- | --- | --- |
| id | BigAutoField | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键，自增 ID |
| name | CharField(30) | VARCHAR(30) | NOT NULL，普通索引 | 作者姓名 |
| country | CharField(20) | VARCHAR(20) | NULL/空串允许 | 国籍（用于作者页国籍过滤） |
| birth_year | SmallIntegerField | SMALLINT | NULL | 出生年份（如 1949） |
| masterpiece | CharField(50) | VARCHAR(50) | NULL/空串 | 代表作名称 |
| created_at | DateTimeField | TEXT(ISO8601) | NOT NULL，auto_now_add | 记录创建时间 |
| updated_at | DateTimeField | TEXT(ISO8601) | NOT NULL，auto_now | 记录最后修改时间 |

**业务规则：**
- `name` 允许重名（不同作者可能同名），不做唯一约束。
- 删除校验：存在关联图书时拒绝删除（由 `book.author_id` 的 `on_delete=PROTECT` 保证）。

### 3.2 出版社表 `publisher`

存储出版社基本信息，对应"出版社管理"页面。

| 字段名 | Django 字段类型 | SQLite 类型 | 约束 | 中文注释 |
| --- | --- | --- | --- | --- |
| id | BigAutoField | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键，自增 ID |
| name | CharField(50) | VARCHAR(50) | NOT NULL，UNIQUE | 出版社名称（唯一） |
| city | CharField(20) | VARCHAR(20) | NULL/空串允许 | 所在城市（用于城市过滤） |
| founded_year | SmallIntegerField | SMALLINT | NULL | 成立年份（如 1951） |
| phone | CharField(20) | VARCHAR(20) | NULL/空串 | 联系电话（如 010-65288961） |
| created_at | DateTimeField | TEXT(ISO8601) | NOT NULL，auto_now_add | 记录创建时间 |
| updated_at | DateTimeField | TEXT(ISO8601) | NOT NULL，auto_now | 记录最后修改时间 |

**业务规则：**
- `name` 唯一，避免重复录入同一出版社。
- 删除校验：存在关联图书时拒绝删除（`on_delete=PROTECT`）。

### 3.3 分类表 `category`

图书分类字典表，对应前端分类下拉与"分类分布"图表。分类从 Mock 枚举升级为数据表，便于后台维护。

| 字段名 | Django 字段类型 | SQLite 类型 | 约束 | 中文注释 |
| --- | --- | --- | --- | --- |
| id | BigAutoField | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键，自增 ID |
| name | CharField(20) | VARCHAR(20) | NOT NULL，UNIQUE | 分类名称（如：文学、科技、历史、艺术、经济、教育） |
| sort_order | IntegerField | INTEGER | NOT NULL，默认 0 | 展示排序，值越小越靠前 |
| created_at | DateTimeField | TEXT(ISO8601) | NOT NULL，auto_now_add | 记录创建时间 |

**初始数据：** 文学、科技、历史、艺术、经济、教育（共 6 条）。

### 3.4 图书表 `book`

核心业务表，对应"图书管理"页面与数据大屏的大部分统计。

| 字段名 | Django 字段类型 | SQLite 类型 | 约束 | 中文注释 |
| --- | --- | --- | --- | --- |
| id | BigAutoField | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键，自增 ID |
| title | CharField(100) | VARCHAR(100) | NOT NULL，普通索引 | 书名 |
| author_id | ForeignKey(author) | INTEGER | NOT NULL，外键索引，on_delete=PROTECT | 作者 ID，关联 `author.id` |
| publisher_id | ForeignKey(publisher) | INTEGER | NOT NULL，外键索引，on_delete=PROTECT | 出版社 ID，关联 `publisher.id` |
| category_id | ForeignKey(category) | INTEGER | NULL，外键索引，on_delete=SET_NULL | 分类 ID，关联 `category.id`；分类删除后置空 |
| isbn | CharField(13) | VARCHAR(13) | NOT NULL，UNIQUE | ISBN 号（10 或 13 位数字，前端正则校验） |
| publish_date | DateField | TEXT(ISO8601) | NOT NULL | 出版日期（用于日期区间过滤） |
| stock | IntegerField | INTEGER | NOT NULL，默认 0，CHECK >= 0 | 库存数量（< 5 时前端标红提示"库存不足"） |
| cover_color | CharField(7) | VARCHAR(7) | NOT NULL，默认 '#4F6BFF' | 封面色值（十六进制，未上传封面图时前端渲染色块封面） |
| cover_image | TextField | TEXT | NULL/空串 | 封面图片（Base64 Data URL，≤1MB；有值时前端优先显示真实封面） |
| intro | TextField | TEXT | NULL/空串 | 图书简介（≤500 字） |
| created_at | DateTimeField | TEXT(ISO8601) | NOT NULL，auto_now_add，普通索引 | 入库时间（用于"最新入库"、"入库趋势"、"今日入库"统计） |
| updated_at | DateTimeField | TEXT(ISO8601) | NOT NULL，auto_now | 最后修改时间 |

**业务规则：**
- `isbn` 全局唯一，防止同一本书重复入库。
- `stock` 不允许为负数（数据库 CHECK 约束 + 表单校验双保险）。
- 列表默认按 `created_at` 倒序排列（与 Mock 层行为一致）。

### 3.5 用户表 `auth_user`（Django 内置）

直接使用 Django 自带的 `django.contrib.auth.models.User`，无需新建表，`migrate` 时自动创建。对应登录页。

| 字段名（常用） | 类型 | 中文注释 |
| --- | --- | --- |
| id | INTEGER | 主键，自增 ID |
| username | VARCHAR(150) | 登录账号（唯一） |
| password | VARCHAR(128) | 密码哈希（PBKDF2，禁止存明文） |
| email | VARCHAR(254) | 邮箱 |
| is_staff | BOOLEAN | 是否可登录 Django Admin 后台 |
| is_active | BOOLEAN | 账号是否启用 |
| date_joined | TEXT(ISO8601) | 注册时间 |
| last_login | TEXT(ISO8601) | 最后登录时间 |

**说明：**
- 登录接口（`POST /api/v1/auth/login`）使用 `django.contrib.auth.authenticate()` 校验，Token 方案可选 DRF SimpleJWT（前端请求头 `Authorization: Bearer <token>` 已在文档中约定）。
- 注册接口（`POST /api/v1/auth/register`）仅接收用户名 + 密码，通过 `User.objects.create_user()` 写入本表（密码自动 PBKDF2 哈希）；`username` 唯一，重复注册返回业务错误。密码在前端表单层做"确认密码"二次输入校验，无需新增字段或新表。
- 登录成功后除返回用户名外，还返回 `isAdmin` 布尔值（`is_superuser` 或 `username == 'admin'`），前端据此控制增删改按钮的可用性。
- 登录 token 使用 DRF `rest_framework.authtoken` 的 `Token` 表（`authtoken_token`：`key` / `user_id` / `created`），通过 `Authorization: Bearer <key>` 解析当前用户，用于后端权限校验与借阅记录归属。

### 3.6 借阅记录表 `borrow_record`

对应新增的"图书借阅"页面，记录每次借阅的图书、借阅人、状态与时间。

| 字段名 | Django 字段类型 | SQLite 类型 | 约束 | 中文注释 |
| --- | --- | --- | --- | --- |
| id | BigAutoField | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键，自增 ID |
| book_id | ForeignKey(book) | INTEGER | NOT NULL，外键索引，on_delete=PROTECT | 借阅图书 ID，关联 `book.id`；图书存在借阅记录时禁止删除 |
| user_id | ForeignKey(auth_user) | INTEGER | NOT NULL，外键索引，on_delete=CASCADE | 借阅人 ID，关联 `auth_user.id` |
| status | CharField(10) | VARCHAR(10) | NOT NULL，默认 `借阅中` | 借阅状态：`借阅中` / `已归还` |
| borrowed_at | DateTimeField | TEXT(ISO8601) | NOT NULL，auto_now_add，普通索引 | 借出时间（借阅页"时间"列与排序依据） |
| returned_at | DateTimeField | TEXT(ISO8601) | NULL | 归还时间；未归还时为空 |

**业务规则：**
- 借阅时校验：图书必须存在、`stock > 0`、同一用户对同一本书不可重复借阅（存在 `status='借阅中'` 记录时拒绝）。
- 借阅成功：`borrow_record` 新增一条 `借阅中` 记录，同时 `book.stock` 减 1（库存实时更新）。
- 归还成功：记录状态改为 `已归还` 并写入 `returned_at`，同时 `book.stock` 加 1。
- 删除图书时若存在借阅记录，由 `PROTECT` 拦截并返回友好提示。

---

## 4. 索引设计

| 表 | 索引字段 | 类型 | 用途 |
| --- | --- | --- | --- |
| author | name | 普通索引 | 作者姓名模糊搜索 |
| publisher | name | UNIQUE | 名称唯一约束 + 搜索 |
| category | name | UNIQUE | 分类名称唯一约束 |
| book | title | 普通索引 | 书名模糊搜索 |
| book | isbn | UNIQUE | ISBN 唯一约束 + 精确查询 |
| book | author_id | 外键索引（Django 自动创建） | 按作者过滤图书、作者作品统计 |
| book | publisher_id | 外键索引（自动） | 按出版社过滤图书、出版物统计 |
| book | category_id | 外键索引（自动） | 按分类过滤、分类分布统计 |
| book | created_at | 普通索引 | 入库趋势按月聚合、最新入库排序 |
| borrow_record | book_id | 外键索引（Django 自动创建） | 按图书查借阅记录、借阅校验 |
| borrow_record | user_id | 外键索引（自动） | 按借阅人查历史、重复借阅校验 |
| borrow_record | borrowed_at | 普通索引 | 借阅页按时间倒序分页 |

> SQLite 下 `LIKE '关键字%'` 前缀匹配可走索引；Mock 层使用的是包含式模糊匹配（`%关键字%`），数据量大时可改用 SQLite FTS5 全文索引扩展。

---

## 5. Django models.py 参考实现

```python
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
        on_delete=models.PROTECT,      # 名下有图书时禁止删除作者
        related_name='books',
        verbose_name='作者',
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,      # 名下有图书时禁止删除出版社
        related_name='books',
        verbose_name='出版社',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,     # 分类删除后图书分类置空
        related_name='books',
        null=True,
        blank=True,
        verbose_name='分类',
    )
    isbn = models.CharField(max_length=13, unique=True, verbose_name='ISBN号')
    publish_date = models.DateField(verbose_name='出版日期')
    stock = models.IntegerField(default=0, verbose_name='库存数量')
    cover_color = models.CharField(
        max_length=7, default='#4F6BFF', verbose_name='封面色值'
    )
    cover_image = models.TextField(blank=True, default='', verbose_name='封面图片（Base64 Data URL）')
    intro = models.TextField(blank=True, default='', verbose_name='图书简介')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='入库时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        db_table = 'book'
        ordering = ['-created_at']     # 默认按入库时间倒序，与前端列表一致
        constraints = [
            models.CheckConstraint(
                check=models.Q(stock__gte=0), name='book_stock_gte_0'
            ),                          # 库存不允许为负数
        ]
        verbose_name = '图书'
        verbose_name_plural = '图书'

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
        on_delete=models.PROTECT,      # 有借阅记录的图书禁止删除
        related_name='borrows',
        verbose_name='借阅图书',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,      # 用户注销时级联删除其借阅记录
        related_name='borrows',
        verbose_name='借阅人',
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_BORROWING, verbose_name='借阅状态'
    )
    borrowed_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='借出时间')
    returned_at = models.DateTimeField(null=True, blank=True, verbose_name='归还时间')

    class Meta:
        db_table = 'borrow_record'
        ordering = ['-borrowed_at', '-id']   # 默认按借出时间倒序
        verbose_name = '借阅记录'
        verbose_name_plural = '借阅记录'

    def __str__(self):
        return f'{self.user.username} - {self.book.title} - {self.status}'
```

> `User` 来自 `from django.contrib.auth.models import User`，本设计不重复建用户表。

---

## 6. 种子数据说明

迁移完成后，可通过 Django Admin、fixtures 或数据迁移脚本灌入与前端 Mock 一致的初始数据：

| 表 | 条数 | 内容来源 |
| --- | --- | --- |
| category | 6 | 文学、科技、历史、艺术、经济、教育 |
| author | 16 | 路遥、余华、莫言、刘慈欣、村上春树、东野圭吾、加西亚·马尔克斯、J.K.罗琳、乔治·奥威尔、海明威、凯文·凯利、吴军、当年明月、贡布里希、曼昆、钱钟书 |
| publisher | 8 | 人民文学出版社、中信出版社、机械工业出版社、电子工业出版社、上海译文出版社、译林出版社、南海出版公司、重庆出版社 |
| book | 40 | 对应各作者代表作（平凡的世界、活着、三体、白夜行、百年孤独等），`cover_color` 从色板 `#4F6BFF / #22C55E / #F59E0B / #8B5CF6 / #EC4899 / #06B6D4 / #F97316 / #84CC16` 循环分配；`created_at` 统一落在当天（按序号递增），保证「最新入库」与「今日入库」都有数据 |
| auth_user | 1 | 超级管理员（`python manage.py createsuperuser` 创建）；`admin` 视为图书管理员 |
| borrow_record | 0 | 初始无借阅记录，由用户在前端借阅后生成 |

建议提供 `python manage.py seed` 自定义命令完成一键灌入，便于开发环境重置。

---

## 7. 前端页面与数据表字段映射

| 前端展示字段 | 来源 | 说明 |
| --- | --- | --- |
| 图书列表-封面色块 | `book.cover_color` + `book.title[0]` | 色块 + 书名首字渲染 |
| 图书列表-作者名 | `book.author.name` | 联表查询（`select_related('author')`） |
| 图书列表-出版社名 | `book.publisher.name` | 联表查询（`select_related('publisher')`） |
| 图书列表-分类标签 | `book.category.name` | 联表查询 |
| 图书列表-库存不足标红 | `book.stock < 5` | 前端判断，后端原样返回 |
| 作者列表-作品数量 | `COUNT(book WHERE author_id = id)` | 聚合注解 `annotate(works_count=Count('books'))` |
| 出版社列表-出版物数量 | `COUNT(book WHERE publisher_id = id)` | 聚合注解 |
| 大屏-图书/作者/出版社总数 | 三表各自 `COUNT(*)` | — |
| 大屏-今日入库 | `COUNT(book WHERE date(created_at) = 今天)` | — |
| 大屏-入库趋势 | 按 `created_at` 月份分组 `COUNT` | 见第 8 节 |
| 大屏-分类分布 | 按 `category` 分组 `COUNT` | — |
| 大屏-Top 出版社 | 按 `publisher` 分组 `COUNT` 取前 6 | — |
| 大屏-最新入库 | `book` 按 `created_at` 倒序取 6 条 | — |
| 借阅页-书名 | `borrow_record.book.title` | 联表查询（`select_related('book')`） |
| 借阅页-借阅人 | `borrow_record.user.username` | 联表查询（`select_related('user')`） |
| 借阅页-状态 | `borrow_record.status` | `借阅中` / `已归还`，前端用不同颜色标签 |
| 借阅页-时间 | `borrow_record.borrowed_at`（归还时附 `returned_at`） | 按借出时间倒序 |

---

## 8. Dashboard 统计 SQL 实现参考

```python
from django.db.models import Count
from django.db.models.functions import TruncMonth
from book.models import Book, Author, Publisher

# 近 12 个月入库趋势
trend = (
    Book.objects
    .annotate(month=TruncMonth('created_at'))
    .values('month')
    .annotate(count=Count('id'))
    .order_by('month')
)

# 分类分布
category_dist = (
    Book.objects
    .values('category__name')
    .annotate(value=Count('id'))
)

# Top 出版社（按在库图书数取前 6）
top_publishers = (
    Publisher.objects
    .annotate(value=Count('books'))
    .order_by('-value')[:6]
    .values('name', 'value')
)

# 最新入库（联表取作者名、出版社名）
latest = (
    Book.objects
    .select_related('author', 'publisher')
    .order_by('-created_at')[:6]
)
```

---

## 9. SQLite 注意事项与后续迁移建议

1. **适用场景**：SQLite 适合开发、演示与小型部署（并发写入低）。若生产环境有多用户并发写入需求，建议迁移 MySQL/PostgreSQL——本设计所有字段类型均为 Django 通用类型，迁移时无需修改模型。
2. **外键约束**：SQLite 默认不强制外键，Django 会在建表时生成外键约束，但需确认连接启用了 `PRAGMA foreign_keys = ON`（Django 4.x+ 默认开启）。
3. **大小写敏感**：SQLite 的 `LIKE` 对 ASCII 默认不区分大小写、对中文无影响；`icontains` 在中文场景行为正常。
4. **并发写入**：SQLite 写锁为库级，管理后台低频写入无压力。
5. **备份**：数据库即 `db.sqlite3` 单文件，直接复制文件即可完成备份。

---

## 10. 预留扩展

以下能力在文档中提及但当前原型未实现，建表可延后：

| 扩展 | 说明 |
| --- | --- |
| 借阅到期提醒 | 在 `borrow_record` 增加 `due_at` 应还时间，配合定时任务生成逾期通知 |
| 封面上传 | 已实现：`book.cover_image` 存 Base64 Data URL（≤1MB），与 `cover_color` 并存，有图优先显示图；如需独立文件存储可改为 `ImageField(upload_to='covers/')` |
| 操作日志表 `operation_log` | 操作人、动作、对象、时间，用于审计 |
| 暗黑模式/主题偏好 | 存 `auth_user` 扩展 Profile 表或前端 localStorage |

---

> 文档维护：后端负责人
> 变更记录：
> - v1.0（2026-11-03）初版发布
> - v1.1（2026-11-04）新增借阅记录表 `borrow_record`、借阅状态与库存联动规则、管理员权限判定说明
