# 图书管理系统 · REST API 接口文档

> 版本：v1.1（新增借阅接口与管理员权限控制）
> 后端：Python + Django（3.2.23 兼容，见附录 B）+ Django REST Framework
> 数据库：SQLite 3（表结构见《database-design.md》，含 `borrow_record` 借阅记录表）
> 前端：Vue 3 + Axios（数据层 `library-admin-web/src/api/index.js`）
> 生成方式：逐页扫描前端页面（login / register / dashboard / book / author / publisher / borrow）实际调用的接口函数，并映射到后端真实路由。

---

## 目录

1. [通用约定](#1-通用约定)
2. [页面与接口映射总览](#2-页面与接口映射总览)
3. [认证接口](#3-认证接口)
4. [字典 / 选项接口](#4-字典--选项接口)
5. [图书接口](#5-图书接口)
6. [作者接口](#6-作者接口)
7. [出版社接口](#7-出版社接口)
8. [Dashboard 聚合接口](#8-dashboard-聚合接口)
9. [借阅接口](#9-借阅接口)
10. [业务规则与错误码](#10-业务规则与错误码)
11. [附录 A：字段与数据库表映射](#11-附录-a字段与数据库表映射)
12. [附录 B：Django 3.2.23 兼容性说明](#12-附录-bdjango-3223-兼容性说明)

---

## 1. 通用约定

### 1.1 BaseURL

| 环境 | BaseURL | 说明 |
| --- | --- | --- |
| 开发环境 | `/api/v1` | Vite 代理：`/api` → `http://127.0.0.1:8000`（见 `vite.config.js`） |
| 直连后端 | `http://127.0.0.1:8000/api/v1` | Django `runserver` |

### 1.2 统一响应体

所有接口返回 JSON，结构统一：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| code | int | `0` 表示成功；非 `0` 表示业务失败（当前约定为 `1`） |
| message | string | 提示文案；失败时为中文错误信息，前端直接 `ElMessage.error` 展示 |
| data | object/array/null | 业务数据；失败时为 `null` |

> 前端 axios 响应拦截器已统一拆包：`code === 0` 时返回 `data`，否则抛出 `Error(message)`。页面层拿到的即本文档中的 `data` 部分。

### 1.3 请求头

| 头 | 值 | 说明 |
| --- | --- | --- |
| Content-Type | `application/json` | POST / PUT 请求 |
| Authorization | `Bearer <token>` | 登录后由前端自动附带（token 存于 `localStorage.library_token`） |

> 后端通过 `library.authentication.BearerTokenAuthentication`（DRF `TokenAuthentication` 子类，`keyword='Bearer'`）解析该请求头得到当前用户。**写操作（图书/作者/出版社的新增、编辑、删除、归还）必须携带管理员 token**，否则返回 `不是管理员，无法操作`。

### 1.4 权限模型

| 角色 | 判定方式 | 可执行操作 |
| --- | --- | --- |
| 图书管理员（admin） | `auth_user.is_superuser = True` 或 `username == 'admin'` | 图书 / 作者 / 出版社的增删改查、借阅、归还、查看全部借阅历史 |
| 普通用户 | 其余已登录账号 | **仅借阅**（`POST /books/{id}/borrow`）、查看列表与借阅历史 |

- 登录接口返回 `isAdmin` 布尔值，前端据此控制按钮显隐与提示。
- 普通用户点击新增/编辑/删除时，前端弹出「不是管理员，无法操作」提示框；即使绕过前端直接调用接口，后端同样拦截。

### 1.5 分页约定

列表接口统一接收 `page` / `pageSize` 查询参数，响应 `data` 结构统一：

```json
{
  "list": [],
  "total": 41,
  "page": 1,
  "pageSize": 10
}
```

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| page | int | 1 | 页码，从 1 开始；非法值自动纠正为 1 |
| pageSize | int | 10 | 每页条数；前端支持 10 / 20 / 50 / 100 |

### 1.6 字段命名

- 接口请求/响应字段统一 **camelCase**（与前端开发文档约定一致）。
- 数据库字段为 snake_case，驼峰转换在后端序列化层完成（`library/serializers.py`）。
- 日期格式：`publishDate` 为 `YYYY-MM-DD`；`createdAt` 为 `YYYY-MM-DD HH:mm`（北京时间）。

---

## 2. 页面与接口映射总览

下表由扫描 `library-admin-web/src/views/**` 各页面的实际调用生成：

| 前端页面 | 页面调用的函数（src/api/index.js） | 真实接口 |
| --- | --- | --- |
| 登录页 `views/login/index.vue` | `mockLogin(username, password)` | `POST /api/v1/auth/login` |
| 注册页 `views/register/index.vue` | `register(username, password)` | `POST /api/v1/auth/register` |
| 数据大屏 `views/dashboard/index.vue` | `getDashboard()` | `GET /api/v1/dashboard` |
| 图书管理 `views/book/index.vue` | `getBooks(query)` | `GET /api/v1/books` |
| 〃 | `createBook(payload)` | `POST /api/v1/books` |
| 〃 | `updateBook(id, payload)` | `PUT /api/v1/books/{id}` |
| 〃 | `deleteBook(id)` | `DELETE /api/v1/books/{id}` |
| 〃 | `getAuthorOptions(keyword)`（远程下拉） | `GET /api/v1/options/authors` |
| 〃 | `getPublisherOptions(keyword)`（远程下拉） | `GET /api/v1/options/publishers` |
| 〃 | `getCategories()`（分类筛选下拉） | `GET /api/v1/dict/categories` |
| 作者管理 `views/author/index.vue` | `getAuthors(query)` | `GET /api/v1/authors` |
| 〃 | `createAuthor(payload)` | `POST /api/v1/authors` |
| 〃 | `updateAuthor(id, payload)` | `PUT /api/v1/authors/{id}` |
| 〃 | `deleteAuthor(id)` | `DELETE /api/v1/authors/{id}` |
| 〃 | `getCountries()`（国籍筛选下拉） | `GET /api/v1/dict/countries` |
| 〃 | `getBooks({ authorId, pageSize: 100 })`（详情抽屉-名下图书） | `GET /api/v1/books` |
| 出版社管理 `views/publisher/index.vue` | `getPublishers(query)` | `GET /api/v1/publishers` |
| 〃 | `createPublisher(payload)` | `POST /api/v1/publishers` |
| 〃 | `updatePublisher(id, payload)` | `PUT /api/v1/publishers/{id}` |
| 〃 | `deletePublisher(id)` | `DELETE /api/v1/publishers/{id}` |
| 〃 | `getCities()`（城市筛选下拉） | `GET /api/v1/dict/cities` |
| 〃 | `getBooks({ publisherId, pageSize: 100 })`（详情抽屉-出版物） | `GET /api/v1/books` |
| 图书借阅 `views/borrow/index.vue` | `getBorrows(query)` | `GET /api/v1/borrows` |
| 〃 | `returnBorrow(id)`（管理员标记归还） | `POST /api/v1/borrows/{id}/return` |
| 图书管理（借阅按钮） | `borrowBook(bookId)` | `POST /api/v1/books/{bookId}/borrow` |

**接口清单汇总（18 个路由）：**

```
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/dict/categories
GET    /api/v1/dict/countries
GET    /api/v1/dict/cities
GET    /api/v1/options/authors
GET    /api/v1/options/publishers
GET    /api/v1/books            POST  /api/v1/books
PUT    /api/v1/books/{id}       DELETE /api/v1/books/{id}
POST   /api/v1/books/{id}/borrow
GET    /api/v1/borrows          POST  /api/v1/borrows/{id}/return
GET    /api/v1/authors          POST  /api/v1/authors
PUT    /api/v1/authors/{id}     DELETE /api/v1/authors/{id}
GET    /api/v1/publishers       POST  /api/v1/publishers
PUT    /api/v1/publishers/{id}  DELETE /api/v1/publishers/{id}
GET    /api/v1/dashboard
```

---

## 3. 认证接口

### 3.1 登录

- **调用页面**：登录页（`mockLogin(username, password)`）
- **接口**：`POST /api/v1/auth/login`

**请求体**

```json
{
  "username": "admin",
  "password": "填入你的管理员登录密码"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| username | string | 是 | 登录账号，对应 `auth_user.username` |
| password | string | 是 | 明文密码，后端使用 Django `authenticate()` 校验哈希 |

**成功响应 data**

```json
{
  "token": "9f2c…(40位hex)",
  "user": { "name": "admin" },
  "isAdmin": true
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| token | string | DRF `Token` 表生成的 40 位 key，后续请求头 `Authorization: Bearer <token>` |
| user.name | string | 用户名（`auth_user.username`） |
| isAdmin | boolean | 是否图书管理员（`is_superuser` 或 `username == 'admin'`），前端据此控制增删改按钮 |

**失败响应**

| 场景 | code | message |
| --- | --- | --- |
| 账号/密码为空 | 1 | `请输入账号和密码` |
| 账号不存在或密码错误 | 1 | `账号或密码错误` |

> 登录页提供"没有账号？立即注册"入口引导用户前往注册页。种子数据内置超级管理员：`admin / 填入你的管理员登录密码`（密码由 seed 命令的环境变量 DJANGO_ADMIN_PASSWORD 指定）（可登录 Django Admin 后台 `/admin/`）。

### 3.2 注册

- **调用页面**：注册页（`register(username, password)`）
- **接口**：`POST /api/v1/auth/register`

**请求体**

```json
{
  "username": "demo",
  "password": "123456"
}
```

| 字段 | 类型 | 必填 | 校验规则 |
| --- | --- | --- | --- |
| username | string | 是 | 非空，≤150 字符，唯一（`auth_user.username`） |
| password | string | 是 | ≥6 位，后端以 PBKDF2 哈希存储（`create_user`） |

**成功响应 data**

```json
{ "id": 2, "username": "demo" }
```

message 为 `注册成功`。前端提示"注册成功，请登录"后跳转回登录页。

**失败响应**

| 场景 | message |
| --- | --- |
| 账号/密码为空 | `请输入账号和密码` |
| 密码不足 6 位 | `密码至少 6 位` |
| 用户名已存在 | `该用户名已被注册` |

---

## 4. 字典 / 选项接口

### 4.1 分类字典

- **调用页面**：图书管理页筛选栏 / 新增编辑弹窗（`getCategories()`）
- **接口**：`GET /api/v1/dict/categories`
- **请求参数**：无
- **响应 data**：分类名称数组（按 `sort_order` 升序），对应 `category` 表

```json
["文学", "科技", "历史", "艺术", "经济", "教育"]
```

### 4.2 国籍字典

- **调用页面**：作者管理页筛选栏（`getCountries()`）
- **接口**：`GET /api/v1/dict/countries`
- **请求参数**：无
- **响应 data**：从 `author.country` 去重得到（排除空值）

```json
["中国", "日本", "哥伦比亚", "英国", "美国"]
```

### 4.3 城市字典

- **调用页面**：出版社管理页筛选栏（`getCities()`）
- **接口**：`GET /api/v1/dict/cities`
- **请求参数**：无
- **响应 data**：从 `publisher.city` 去重得到（排除空值）

```json
["上海", "南京", "北京", "海口", "重庆"]
```

### 4.4 作者远程搜索选项

- **调用页面**：图书管理页筛选栏与表单（`getAuthorOptions(keyword)`）
- **接口**：`GET /api/v1/options/authors`

| 查询参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 姓名模糊匹配（不区分大小写），为空时返回前 20 条 |

**响应 data**（最多 20 条）

```json
[{ "id": 2, "name": "余华" }]
```

### 4.5 出版社远程搜索选项

- **调用页面**：图书管理页筛选栏与表单（`getPublisherOptions(keyword)`）
- **接口**：`GET /api/v1/options/publishers`

| 查询参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 名称模糊匹配，最多返回 20 条 |

**响应 data**

```json
[{ "id": 1, "name": "人民文学出版社" }]
```

---

## 5. 图书接口

> **权限要求**：5.2 新增 / 5.3 编辑 / 5.4 删除 仅图书管理员可调用（需在请求头携带管理员 token）。非管理员调用统一返回：

```json
{ "code": 1, "message": "不是管理员，无法操作", "data": null }
```

> 第 6 章作者、第 7 章出版社的新增 / 编辑 / 删除同样适用此权限要求；列表查询（GET）对全部登录用户开放。

### 5.1 图书分页列表

- **调用页面**：图书管理页（`getBooks(query)`）；作者/出版社详情抽屉（`getBooks({authorId|publisherId, pageSize:100})`）
- **接口**：`GET /api/v1/books`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 书名 / ISBN 模糊搜索（OR 关系） |
| authorId | int | 否 | 按作者过滤（`book.author_id`） |
| publisherId | int | 否 | 按出版社过滤（`book.publisher_id`） |
| category | string | 否 | 按分类名称过滤（如 `文学`），对应 `category.name` |
| dateStart | string | 否 | 出版日期起（`YYYY-MM-DD`），需与 dateEnd 同时传 |
| dateEnd | string | 否 | 出版日期止（`YYYY-MM-DD`） |
| page | int | 否 | 页码，默认 1 |
| pageSize | int | 否 | 每页条数，默认 10 |

> 排序固定为 `created_at` 倒序（最新入库在前），与 Mock 层行为一致。

**响应 data**

```json
{
  "list": [
    {
      "id": 1,
      "title": "平凡的世界",
      "authorId": 1,
      "publisherId": 1,
      "isbn": "9787100000000",
      "category": "文学",
      "publishDate": "2005-04-08",
      "stock": 0,
      "intro": "《平凡的世界》是路遥的代表作品之一，馆藏热门图书。",
      "cover": { "color": "#4F6BFF", "image": "" },
      "createdAt": "2026-11-04 09:30",
      "authorName": "路遥",
      "publisherName": "人民文学出版社"
    }
  ],
  "total": 41,
  "page": 1,
  "pageSize": 10
}
```

**图书对象字段说明**

| 字段 | 类型 | 数据库来源 | 说明 |
| --- | --- | --- | --- |
| id | int | `book.id` | 主键 |
| title | string | `book.title` | 书名 |
| authorId | int | `book.author_id` | 作者外键 |
| publisherId | int | `book.publisher_id` | 出版社外键 |
| isbn | string | `book.isbn` | ISBN，全局唯一 |
| category | string | `category.name`（JOIN） | 分类名称；分类被删除时为空串 `""` |
| publishDate | string | `book.publish_date` | `YYYY-MM-DD` |
| stock | int | `book.stock` | 库存，≥0；< 5 时前端标红"库存不足" |
| intro | string | `book.intro` | 简介 |
| cover.color | string | `book.cover_color` | 封面色值，未上传封面图时前端渲染色块 |
| cover.image | string | `book.cover_image` | 封面图片 Base64 Data URL；空串表示未上传，前端回退到色块 |
| createdAt | string | `book.created_at` | `YYYY-MM-DD HH:mm` |
| authorName | string | `author.name`（JOIN） | 冗余展示字段 |
| publisherName | string | `publisher.name`（JOIN） | 冗余展示字段 |

### 5.2 新增图书

- **调用页面**：图书管理页新增弹窗（`createBook(payload)`）
- **接口**：`POST /api/v1/books`

**请求体**

```json
{
  "title": "平凡的世界",
  "authorId": 1,
  "publisherId": 1,
  "isbn": "9787100000000",
  "category": "文学",
  "publishDate": "2005-04-08",
  "stock": 10,
  "intro": "图书简介（可选）",
  "coverImage": "data:image/png;base64,...（可选，Base64 Data URL）"
}
```

| 字段 | 类型 | 必填 | 校验规则 |
| --- | --- | --- | --- |
| title | string | 是 | 非空，≤100 字 |
| authorId | int | 是 | 必须存在于 `author` 表 |
| publisherId | int | 是 | 必须存在于 `publisher` 表 |
| isbn | string | 是 | 10/13 位，全局唯一（唯一约束） |
| category | string | 否 | 分类名称，必须存在于 `category` 表；可传空 |
| publishDate | string | 否 | `YYYY-MM-DD`，缺省为当天 |
| stock | int | 否 | ≥0，默认 0 |
| intro | string | 否 | ≤500 字 |
| coverImage | string | 否 | Base64 Data URL；前端限制 JPG/PNG/WEBP、≤1MB；传空串表示清除封面 |

**响应 data**：完整图书对象（同 5.1 list 元素，含 `cover.color` 服务端自动生成、`cover.image` 为提交的封面图）。

**失败响应**

| 场景 | message |
| --- | --- |
| 书名/ISBN 为空 | `书名不能为空` / `ISBN 不能为空` |
| authorId / publisherId 无效 | `请选择作者` / `作者不存在` / `出版社不存在` |
| category 名称不存在 | `分类「XX」不存在` |
| ISBN 重复 | `ISBN 已存在，请勿重复入库` |

### 5.3 编辑图书

- **调用页面**：图书管理页编辑弹窗（`updateBook(id, payload)`）
- **接口**：`PUT /api/v1/books/{id}`
- **请求体**：同 5.2
- **响应 data**：更新后的完整图书对象
- **失败响应**：`图书不存在`（id 无效）、`ISBN 已存在`（与其他图书冲突）

### 5.4 删除图书

- **调用页面**：图书管理页行内删除（`deleteBook(id)`）
- **接口**：`DELETE /api/v1/books/{id}`
- **响应 data**：`null`，message 为 `删除成功`
- **失败响应**：`图书不存在`

---

## 6. 作者接口

### 6.1 作者分页列表

- **调用页面**：作者管理页（`getAuthors(query)`）
- **接口**：`GET /api/v1/authors`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 姓名模糊搜索 |
| country | string | 否 | 按国籍精确过滤 |
| page / pageSize | int | 否 | 分页，同通用约定 |

**响应 data**

```json
{
  "list": [
    {
      "id": 2,
      "name": "余华",
      "country": "中国",
      "birthYear": 1960,
      "masterpiece": "活着",
      "createdAt": "2026-02-08 10:26",
      "worksCount": 4,
      "color": "#F59E0B"
    }
  ],
  "total": 16,
  "page": 1,
  "pageSize": 10
}
```

| 字段 | 类型 | 数据库来源 | 说明 |
| --- | --- | --- | --- |
| id | int | `author.id` | 主键 |
| name | string | `author.name` | 姓名 |
| country | string | `author.country` | 国籍 |
| birthYear | int/null | `author.birth_year` | 出生年份 |
| masterpiece | string | `author.masterpiece` | 代表作 |
| createdAt | string | `author.created_at` | 创建时间 |
| worksCount | int | `COUNT(book)` 聚合 | 名下图书数量 |
| color | string | 服务端按姓名生成 | 头像底色 |

### 6.2 新增作者

- **调用页面**：作者管理页新增弹窗（`createAuthor(payload)`）
- **接口**：`POST /api/v1/authors`

**请求体**

```json
{ "name": "余华", "country": "中国", "birthYear": 1960, "masterpiece": "活着" }
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | ≤30 字；允许重名 |
| country | string | 否 | ≤20 字 |
| birthYear | int | 否 | 4 位年份 |
| masterpiece | string | 否 | ≤50 字 |

**响应 data**：作者对象（`worksCount` 为 0）。失败：`作者姓名不能为空`。

### 6.3 编辑作者

- **接口**：`PUT /api/v1/authors/{id}`
- **请求体 / 响应**：同 6.2。失败：`作者不存在`。

### 6.4 删除作者（删除保护）

- **接口**：`DELETE /api/v1/authors/{id}`
- **删除保护**：名下存在图书时由数据库 `PROTECT` 约束拦截，返回：

```json
{ "code": 1, "message": "该作者名下存在 4 本图书，无法删除", "data": null }
```

- 成功：`data` 为 `null`，message 为 `删除成功`。

---

## 7. 出版社接口

### 7.1 出版社分页列表

- **调用页面**：出版社管理页（`getPublishers(query)`）
- **接口**：`GET /api/v1/publishers`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 名称模糊搜索 |
| city | string | 否 | 按城市精确过滤 |
| page / pageSize | int | 否 | 分页 |

**响应 data**

```json
{
  "list": [
    {
      "id": 7,
      "name": "南海出版公司",
      "city": "海口",
      "foundedYear": 1988,
      "phone": "0898-65350227",
      "createdAt": "2026-05-12 10:00",
      "bookCount": 5
    }
  ],
  "total": 8,
  "page": 1,
  "pageSize": 10
}
```

| 字段 | 类型 | 数据库来源 | 说明 |
| --- | --- | --- | --- |
| id | int | `publisher.id` | 主键 |
| name | string | `publisher.name` | 名称（唯一） |
| city | string | `publisher.city` | 所在城市 |
| foundedYear | int/null | `publisher.founded_year` | 成立年份 |
| phone | string | `publisher.phone` | 联系电话 |
| createdAt | string | `publisher.created_at` | 创建时间 |
| bookCount | int | `COUNT(book)` 聚合 | 出版物数量 |

### 7.2 新增出版社

- **接口**：`POST /api/v1/publishers`

**请求体**

```json
{ "name": "中信出版社", "city": "北京", "foundedYear": 1988, "phone": "010-84849055" }
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | ≤50 字，**唯一** |
| city | string | 否 | ≤20 字 |
| foundedYear | int | 否 | 4 位年份 |
| phone | string | 否 | ≤20 字 |

**响应 data**：出版社对象（`bookCount` 为 0）。
**失败**：`出版社名称不能为空` / `该出版社已存在`（唯一约束）。

### 7.3 编辑出版社

- **接口**：`PUT /api/v1/publishers/{id}`
- **请求体 / 响应**：同 7.2。失败：`出版社不存在` / `该出版社已存在`。

### 7.4 删除出版社（删除保护）

- **接口**：`DELETE /api/v1/publishers/{id}`
- **删除保护**：名下存在图书时返回：

```json
{ "code": 1, "message": "该出版社名下存在 6 本图书，无法删除", "data": null }
```

---

## 8. Dashboard 聚合接口

### 8.1 首页数据大屏

- **调用页面**：数据大屏（`getDashboard()`）
- **接口**：`GET /api/v1/dashboard`
- **请求参数**：无
- **说明**：一次请求聚合返回大屏所需的全部数据（指标卡 + 3 图表 + 最新入库）。

**响应 data**

```json
{
  "summary": {
    "bookCount": 41,
    "authorCount": 16,
    "publisherCount": 8,
    "todayCount": 2,
    "bookTrend": 67,
    "authorTrend": 0,
    "publisherTrend": 100,
    "todayTrend": 100
  },
  "trend": [
    { "month": "25-12", "count": 3 },
    { "month": "26-01", "count": 3 }
  ],
  "categoryDist": [
    { "name": "文学", "value": 27 },
    { "name": "科技", "value": 6 }
  ],
  "topPublishers": [
    { "name": "人民文学出版社", "value": 6 }
  ],
  "latest": [
    {
      "id": 1,
      "title": "平凡的世界",
      "authorName": "路遥",
      "publisherName": "人民文学出版社",
      "category": "文学",
      "cover": { "color": "#4F6BFF", "image": "" },
      "createdAt": "2026-11-04 09:30"
    }
  ]
}
```

**summary 字段说明**

| 字段 | 说明 |
| --- | --- |
| bookCount | 图书总数（`book` 表 COUNT） |
| authorCount | 作者总数 |
| publisherCount | 出版社总数 |
| todayCount | 今日入库图书数（`created_at` 为当天） |
| bookTrend | 本月入库环比上月（%），上月为 0 时：本月 >0 记 100，否则 0 |
| authorTrend | 作者本月新增环比（%），算法同上 |
| publisherTrend | 出版社本月新增环比（%），算法同上 |
| todayTrend | 今日入库环比昨日（%），算法同上 |

**其他区块**

| 字段 | 说明 | 前端图表 |
| --- | --- | --- |
| trend | 近 12 个月入库量，月份格式 `YY-MM`，按时间升序 | 折线图 |
| categoryDist | 各分类图书数量（仅返回 value > 0），按数量降序 | 玫瑰图/饼图 |
| topPublishers | 图书数量 Top 6 出版社（仅返回 value > 0） | 保留字段，当前前端首页已改为「每日好书推荐」，不再展示该图表 |
| latest | 最新入库 6 本图书，字段同图书对象（5.1）；前端「每日好书推荐」按当天日期在此列表内轮换展示摘句 | 最新入库列表 |

---

## 9. 借阅接口

### 9.1 借阅图书

- **调用页面**：图书管理页行内「借阅」按钮（`borrowBook(bookId)`）
- **接口**：`POST /api/v1/books/{id}/borrow`
- **请求体**：无（借阅人取自请求头 token 解析出的当前用户）
- **权限**：全部登录用户可调用（管理员亦可借阅）

**成功响应 data**

```json
{
  "id": 1,
  "bookId": 3,
  "bookTitle": "活着",
  "userId": 2,
  "userName": "zhaoliu",
  "status": "借阅中",
  "borrowedAt": "2026-11-04 19:30",
  "returnedAt": null,
  "stock": 3
}
```

| 字段 | 类型 | 数据库来源 | 说明 |
| --- | --- | --- | --- |
| id | int | `borrow_record.id` | 借阅记录主键 |
| bookId / bookTitle | int / string | `book.id` / `book.title` | 图书信息 |
| userId / userName | int / string | `auth_user.id` / `auth_user.username` | 借阅人信息 |
| status | string | `borrow_record.status` | 固定为 `借阅中` |
| borrowedAt | string | `borrow_record.borrowed_at` | 借出时间 `YYYY-MM-DD HH:mm` |
| returnedAt | string/null | `borrow_record.returned_at` | 未归还时为 `null` |
| stock | int | `book.stock` | **借阅后的最新库存**（原库存 -1），前端可直接刷新列表 |

**失败响应**

| 场景 | message |
| --- | --- |
| 图书不存在 | `图书不存在` |
| 库存为 0 | `该图书已无库存，无法借阅` |
| 同一用户重复借阅同一本书 | `你已借阅该图书且尚未归还` |
| 未携带或 token 无效 | `请先登录` |

### 9.2 借阅历史列表

- **调用页面**：图书借阅页（`getBorrows(query)`）
- **接口**：`GET /api/v1/borrows`
- **权限**：全部登录用户可查看所有用户的借阅历史

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 书名 / 借阅人模糊搜索（OR 关系） |
| status | string | 否 | 按状态精确过滤：`借阅中` / `已归还` |
| page | int | 否 | 页码，默认 1 |
| pageSize | int | 否 | 每页条数，默认 10 |

**响应 data**（分页结构同 1.5）

```json
{
  "list": [
    {
      "id": 1,
      "bookId": 3,
      "bookTitle": "活着",
      "bookIsbn": "9787100000137",
      "userId": 2,
      "userName": "zhaoliu",
      "status": "借阅中",
      "borrowedAt": "2026-11-04 19:30",
      "returnedAt": null
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 10
}
```

> 排序固定为 `borrowed_at` 倒序（最新借阅在前）。

### 9.3 归还图书

- **调用页面**：图书借阅页行内「归还」按钮（`returnBorrow(id)`）
- **接口**：`POST /api/v1/borrows/{id}/return`
- **请求体**：无
- **权限**：**仅图书管理员**

**成功响应 data**：更新后的借阅记录对象（`status` 变为 `已归还`，`returnedAt` 写入当前时间，并附最新 `stock`）。

**失败响应**

| 场景 | message |
| --- | --- |
| 记录不存在 | `借阅记录不存在` |
| 已归还过 | `该借阅记录已归还` |
| 非管理员 | `不是管理员，无法操作` |

---

## 10. 业务规则与错误码

### 10.1 错误码

| code | 含义 | 前端行为 |
| --- | --- | --- |
| 0 | 成功 | 正常渲染 |
| 1 | 业务失败（校验失败、唯一约束、删除保护、对象不存在等） | axios 拦截器抛出 `Error(message)`，页面 `ElMessage.error` 展示 |

> HTTP 状态码统一为 200；业务成败只看 `code`。未匹配路由返回 Django 默认 404。

### 10.2 业务规则

| 规则 | 实现 |
| --- | --- |
| 作者/出版社删除保护 | `book.author_id` / `book.publisher_id` 外键 `on_delete=PROTECT`，删除前返回名下图书数量提示 |
| 分类删除置空 | `book.category_id` 外键 `on_delete=SET_NULL`，图书保留且 category 返回空串 |
| ISBN 唯一 | `book.isbn` UNIQUE 约束，新增/编辑冲突时返回友好提示 |
| 出版社名称唯一 | `publisher.name` UNIQUE 约束 |
| 库存非负 | `book.stock` CHECK ≥ 0 + 前端表单校验 |
| 作者允许重名 | `author.name` 仅普通索引，无唯一约束 |
| 图书默认排序 | `created_at` 倒序（最新入库在前） |
| 用户名唯一 | `auth_user.username` 唯一约束，重复注册返回"该用户名已被注册" |
| 密码存储 | 仅存 PBKDF2 哈希（`create_user`），接口禁止返回密码字段 |
| 管理员权限 | 写操作（图书/作者/出版社增删改、归还）校验 `is_superuser` 或 `username='admin'`，否则返回 `不是管理员，无法操作` |
| 借阅库存联动 | 借阅成功 `book.stock -= 1`；归还成功 `book.stock += 1`，均在事务内与 `borrow_record` 同步更新 |
| 借阅前置校验 | 库存 > 0 且该用户对同一本书无 `借阅中` 记录，否则拒绝 |
| 图书删除保护（借阅） | `borrow_record.book` 外键 `on_delete=PROTECT`，存在借阅记录的图书不可删除 |

---

## 11. 附录 A：字段与数据库表映射

| 接口字段（camelCase） | 数据库字段（snake_case） | 所在表 |
| --- | --- | --- |
| Book.id / Author.id / Publisher.id | id | book / author / publisher |
| title | title | book |
| authorId / authorName | author_id / author.name | book ⋈ author |
| publisherId / publisherName | publisher_id / publisher.name | book ⋈ publisher |
| category | category.name | book ⋈ category |
| isbn | isbn | book |
| publishDate | publish_date | book |
| stock | stock | book |
| intro | intro | book |
| cover.color | cover_color | book |
| createdAt | created_at | 各业务表 |
| country / birthYear / masterpiece | country / birth_year / masterpiece | author |
| city / foundedYear / phone | city / founded_year / phone | publisher |
| worksCount / bookCount | COUNT(book.id) 聚合 | author / publisher |
| borrow.record id | borrow_record.id | borrow_record |
| bookId / bookTitle | book_id / book.title | borrow_record ⋈ book |
| userId / userName | user_id / auth_user.username | borrow_record ⋈ auth_user |
| borrow.status | status | borrow_record |
| borrowedAt / returnedAt | borrowed_at / returned_at | borrow_record |

> 完整表结构、索引与约束定义见《database-design.md》第 3、4 节。

---

## 12. 附录 B：Django 3.2.23 兼容性说明

当前开发环境安装的是 Django 6.1.2，接口行为与本文档完全一致。若部署目标为 **Django 3.2.23**，仅有以下代码层差异需调整（接口契约不变）：

| 位置 | Django 6.x 写法 | Django 3.2 写法 |
| --- | --- | --- |
| `models.py` 库存 CHECK 约束 | `models.CheckConstraint(condition=Q(stock__gte=0), name=...)` | `models.CheckConstraint(check=Q(stock__gte=0), name=...)` |
| `settings.py` 邮箱配置 | `MAILERS = {...}`（6.x 新格式） | `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` |
| `settings.py` 默认主键 | 无需配置 | 建议 `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'` |
| `settings.py` Token 认证 | `rest_framework.authtoken` 写法一致 | 需将 `'rest_framework.authtoken'` 加入 `INSTALLED_APPS` 并执行 `migrate`（3.2 同样适用） |

DRF 3.18、django-cors-headers 4.x 均兼容 Django 3.2，路由与视图代码无需改动。

---

> 文档生成说明：接口清单通过扫描 `library-admin-web/src/views` 下 5 个页面的实际 API 调用获得，并与后端 `library/urls.py`、`library/views.py` 逐一核对。所有接口已通过 PowerShell 冒烟测试与浏览器端到端验证。
