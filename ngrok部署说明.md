# 图书管理系统 · ngrok 公网部署说明

> 部署方式：ngrok 单入口隧道 → Vite 开发服务器（5173）→ `/api` 代理 → Django（8000）
> 当前公网地址：**https://<填入你的 ngrok 公网域名>**

## 1. 架构与访问链路

```
公网浏览器
   │ HTTPS
   ▼
ngrok (https://<填入你的 ngrok 公网域名>)
   │ 转发到本机
   ▼
Vite Dev Server 127.0.0.1:5173  ── /api ──▶  Django 127.0.0.1:8000  ──▶  SQLite
```

- 只有一个公网入口：页面与接口同源，不存在跨域问题。
- `/api` 由 Vite 代理转发到 Django，`changeOrigin: true` 会把 Host 重写为 `127.0.0.1:8000`。
- ngrok 负责 HTTPS 证书与公网转发，无需额外配置证书。

## 2. 首次准备

1. 安装 ngrok（本机已完成，版本 3.39.13）：`ngrok version`
   - 若版本过低（如 3.3.1）会在启动隧道时报 `ERR_NGROK_121`，先执行 `ngrok update --channel stable` 升级。
2. 配置 authtoken（只需一次）：
   ```powershell
   ngrok config add-authtoken <填入你的 ngrok authtoken 密钥>
   ngrok config check
   ```
3. 后端依赖与数据库迁移（依赖已装好，换机器时重新安装 Django / DRF / django-cors-headers）：
   ```powershell
   cd d:\test\library_admin\library_admin_api
   python manage.py migrate
   ```
4. 前端依赖：
   ```powershell
   cd d:\test\library_admin\library-admin-web
   npm install
   ```

## 3. 启动（三个终端，按顺序）

**终端 1 · Django 后端**

```powershell
cd d:\test\library_admin\library_admin_api
$env:DJANGO_DEBUG="0"      # 公网模式：关闭 DEBUG
python manage.py runserver 127.0.0.1:8000
```

**终端 2 · Vite 前端**

```powershell
cd d:\test\library_admin\library-admin-web
npm run dev
```

**终端 3 · ngrok 隧道**

```powershell
ngrok http 127.0.0.1:5173
```

启动后终端会打印形如 `Forwarding https://xxxx.ngrok-free.dev -> http://127.0.0.1:5173` 的公网地址；
也可打开本地管理台 http://127.0.0.1:4040 查看请求日志。

> 免费版的随机域名在每次重启 ngrok 后都会变化。若已在 ngrok 控制台申请固定域名，可改用：
> `ngrok http --domain=你的固定域名 127.0.0.1:5173`

## 4. 停止

在各终端按 `Ctrl + C` 即可。也可只结束隧道进程：

```powershell
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
```

> 只关闭 ngrok 后，本地 http://localhost:5173 仍可继续使用；关闭 Django 后前端页面可打开但接口会失败。

## 5. 本次涉及的配置改动

### Vite（`library-admin-web/vite.config.js`）

```js
server: {
  port: 5173,
  host: '127.0.0.1',          // 固定 IPv4 回环，供 ngrok 转发
  strictPort: true,           // 端口被占用直接报错，避免隧道指向错误端口
  allowedHosts: ['.ngrok-free.app', '.ngrok.app', '.ngrok.io', '.ngrok-free.dev'],
  proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
}
```

- `allowedHosts` 用于放行 ngrok 域名（Vite 5.4+ 默认拦截未知 Host，否则返回 `Blocked request`）。

### Django（`library_admin_api/library_admin_api/settings.py`）

```python
DEBUG = os.environ.get('DJANGO_DEBUG', '0') in ('1', 'true', 'True')
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]',
                 '.ngrok-free.app', '.ngrok-free.dev', '.ngrok.app', '.ngrok.io']
CSRF_TRUSTED_ORIGINS = ['https://*.ngrok-free.app', 'https://*.ngrok-free.dev',
                        'https://*.ngrok.app', 'https://*.ngrok.io',
                        'http://localhost:5173', 'http://127.0.0.1:5173']
```

- **DEBUG 默认关闭**：公网不返回调试页与堆栈；本地需要调试时临时执行 `$env:DJANGO_DEBUG="1"` 再启动。
- `ALLOWED_HOSTS` 使用前导点形式匹配所有 ngrok 子域。
- 静态资源：前端静态文件由 Vite 提供；公网入口只代理 `/api`，Django Admin（`/admin/`）未对外暴露，因此 `DEBUG=False` 不影响页面访问。若本地需要 Admin 样式，使用 `DJANGO_DEBUG=1` 启动即可。
- 未修改 `SECRET_KEY`、数据库文件与业务代码，数据库现有数据保持不变。

## 6. 部署验证结果（通过公网 HTTPS 地址实测）

| 项目 | 结果 |
| --- | --- |
| 首页 `GET /` | 200，返回 Vue 应用 HTML |
| 登录 `POST /api/v1/auth/login`（admin） | `code=0`，`isAdmin=true` |
| 图书查询 `GET /api/v1/books` | `code=0`，`total=43` |
| 新增图书 `POST /api/v1/books` | `code=0`，总数 43 → 44 |
| 编辑图书 `PUT /api/v1/books/{id}` | `code=0`，标题/库存更新成功 |
| 删除图书 `DELETE /api/v1/books/{id}` | `code=0`，总数恢复 43 |
| 数据库读写 | SQLite 持久化正常，测试数据已删除，原有 43 条数据未改动 |

## 7. 注意事项

1. **公网暴露**：免费 ngrok 地址任何拿到链接的人都能访问，`admin` 的默认密码请填入你的管理员登录密码，并尽快改成强密码（`python manage.py changepassword admin`）。
2. 首次用浏览器打开免费域名时，可能先看到 ngrok 的提示页（“You are about to visit…”），点击 **Visit Site** 后正常进入，之后会写入 Cookie 不再提示。
3. 免费版会把浏览器发出的请求判定为“浏览器访问”并返回提示页（`text/plain`，约 254 字节），导致接口拿不到 JSON。前端已在 axios 请求拦截器中统一附带 `ngrok-skip-browser-warning: 1` 跳过该提示页（见 `src/api/index.js`），无需额外操作。
4. Vite 为开发服务器，HMR 的 WebSocket 经 ngrok 转发时控制台可能出现连接告警，不影响页面与接口功能。正式生产建议 `npm run build` 后用 Nginx/静态托管。
5. SQLite 为单写者数据库，适合当前演示/小规模使用；并发要求高时建议迁移 PostgreSQL/MySQL。
6. 关闭 ngrok 后公网地址立即失效，本地开发不受影响。
7. 不要把 ngrok authtoken、Django `SECRET_KEY`、数据库文件提交到代码仓库或发给他人。
