// ============================================================
// Mock 数据层（localStorage 持久化 + 模拟网络延迟）
// 接口形态与开发文档中的 RESTful 约定保持一致，
// 将来接入真实后端时，只需用 axios 重写本文件中的各函数实现。
// ============================================================

const DB_KEY = 'library_admin_db_v1'

const CATEGORIES = ['文学', '科技', '历史', '艺术', '经济', '教育']
const COVER_COLORS = ['#4F6BFF', '#22C55E', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#84CC16']

const pad = (n) => String(n).padStart(2, '0')
const fmtDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const fmtDateTime = (d) => `${fmtDate(d)} ${pad(d.getHours())}:${pad(d.getMinutes())}`
const delay = (ms = 200) => new Promise((r) => setTimeout(r, ms))

/* ---------------- 种子数据 ---------------- */

const AUTHORS_SEED = [
  { name: '路遥', country: '中国', birthYear: 1949, masterpiece: '平凡的世界' },
  { name: '余华', country: '中国', birthYear: 1960, masterpiece: '活着' },
  { name: '莫言', country: '中国', birthYear: 1955, masterpiece: '红高粱家族' },
  { name: '刘慈欣', country: '中国', birthYear: 1963, masterpiece: '三体' },
  { name: '村上春树', country: '日本', birthYear: 1949, masterpiece: '挪威的森林' },
  { name: '东野圭吾', country: '日本', birthYear: 1958, masterpiece: '白夜行' },
  { name: '加西亚·马尔克斯', country: '哥伦比亚', birthYear: 1927, masterpiece: '百年孤独' },
  { name: 'J.K.罗琳', country: '英国', birthYear: 1965, masterpiece: '哈利·波特与魔法石' },
  { name: '乔治·奥威尔', country: '英国', birthYear: 1903, masterpiece: '1984' },
  { name: '海明威', country: '美国', birthYear: 1899, masterpiece: '老人与海' },
  { name: '凯文·凯利', country: '美国', birthYear: 1952, masterpiece: '失控' },
  { name: '吴军', country: '美国', birthYear: 1967, masterpiece: '浪潮之巅' },
  { name: '当年明月', country: '中国', birthYear: 1979, masterpiece: '明朝那些事儿' },
  { name: '贡布里希', country: '英国', birthYear: 1909, masterpiece: '艺术的故事' },
  { name: '曼昆', country: '美国', birthYear: 1958, masterpiece: '经济学原理' },
  { name: '钱钟书', country: '中国', birthYear: 1910, masterpiece: '围城' },
]

const PUBLISHERS_SEED = [
  { name: '人民文学出版社', city: '北京', foundedYear: 1951, phone: '010-65288961' },
  { name: '中信出版社', city: '北京', foundedYear: 1988, phone: '010-84849055' },
  { name: '机械工业出版社', city: '北京', foundedYear: 1952, phone: '010-88379639' },
  { name: '电子工业出版社', city: '北京', foundedYear: 1982, phone: '010-88254000' },
  { name: '上海译文出版社', city: '上海', foundedYear: 1978, phone: '021-62460100' },
  { name: '译林出版社', city: '南京', foundedYear: 1988, phone: '025-83302800' },
  { name: '南海出版公司', city: '海口', foundedYear: 1988, phone: '0898-65350227' },
  { name: '重庆出版社', city: '重庆', foundedYear: 1950, phone: '023-68809799' },
]

// [书名, 作者索引, 分类]
const BOOKS_SEED = [
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

function seed() {
  const now = new Date()

  const authors = AUTHORS_SEED.map((a, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - (i % 12), ((i * 7) % 27) + 1, 9 + (i % 8), (i * 13) % 60)
    return { id: `a${i + 1}`, ...a, createdAt: fmtDateTime(d) }
  })

  const publishers = PUBLISHERS_SEED.map((p, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - ((i * 2) % 12), ((i * 11) % 27) + 1, 10, 0)
    return { id: `p${i + 1}`, ...p, createdAt: fmtDateTime(d) }
  })

  const books = BOOKS_SEED.map(([title, ai, category], i) => {
    const created = new Date(now.getFullYear(), now.getMonth() - (i % 12), ((i * 5) % 27) + 1, 8 + (i % 10), (i * 17) % 60)
    const pub = new Date(2000 + ((i * 5) % 25), (i * 3) % 12, ((i * 7) % 28) + 1)
    return {
      id: `b${i + 1}`,
      title,
      authorId: authors[ai].id,
      publisherId: publishers[i % publishers.length].id,
      isbn: `9787${String(100000000 + i * 137)}`,
      category,
      publishDate: fmtDate(pub),
      stock: (i * 7) % 23,
      intro: `《${title}》是${authors[ai].name}的代表作品之一，馆藏热门图书。`,
      cover: { color: COVER_COLORS[i % COVER_COLORS.length] },
      createdAt: fmtDateTime(created),
    }
  })

  // 保证“今日入库”有演示数据
  books[0].createdAt = fmtDateTime(now)
  books[1].createdAt = fmtDateTime(now)

  return { authors, publishers, books }
}

/* ---------------- 持久化 ---------------- */

function load() {
  try {
    const raw = localStorage.getItem(DB_KEY)
    if (raw) return JSON.parse(raw)
  } catch (e) {
    // 数据损坏时重新播种
  }
  const db = seed()
  localStorage.setItem(DB_KEY, JSON.stringify(db))
  return db
}

let db = load()

function save() {
  localStorage.setItem(DB_KEY, JSON.stringify(db))
}

/* ---------------- 通用工具 ---------------- */

function paginate(list, q) {
  const page = q.page || 1
  const pageSize = q.pageSize || 10
  return {
    list: list.slice((page - 1) * pageSize, page * pageSize),
    total: list.length,
    page,
    pageSize,
  }
}

function withRefs(b) {
  return {
    ...b,
    authorName: db.authors.find((a) => a.id === b.authorId)?.name || '-',
    publisherName: db.publishers.find((p) => p.id === b.publisherId)?.name || '-',
  }
}

const avatarColor = (name) => COVER_COLORS[(name.charCodeAt(0) || 0) % COVER_COLORS.length]

/* ---------------- 认证 ---------------- */

export async function mockLogin() {
  await delay(400)
  return { token: `mock-token-${Date.now()}`, user: { name: '管理员' } }
}

/* ---------------- 字典 / 选项 ---------------- */

export async function getCategories() {
  await delay(60)
  return [...CATEGORIES]
}

export async function getCountries() {
  await delay(60)
  return [...new Set(db.authors.map((a) => a.country))].filter(Boolean)
}

export async function getCities() {
  await delay(60)
  return [...new Set(db.publishers.map((p) => p.city))].filter(Boolean)
}

export async function getAuthorOptions(keyword = '') {
  await delay(150)
  return db.authors
    .filter((a) => a.name.toLowerCase().includes(keyword.toLowerCase()))
    .slice(0, 20)
    .map((a) => ({ id: a.id, name: a.name }))
}

export async function getPublisherOptions(keyword = '') {
  await delay(150)
  return db.publishers
    .filter((p) => p.name.toLowerCase().includes(keyword.toLowerCase()))
    .slice(0, 20)
    .map((p) => ({ id: p.id, name: p.name }))
}

/* ---------------- 图书 ---------------- */

export async function getBooks(q = {}) {
  await delay()
  let list = [...db.books]
  if (q.keyword) {
    const k = q.keyword.toLowerCase()
    list = list.filter((b) => b.title.toLowerCase().includes(k) || b.isbn.includes(k))
  }
  if (q.authorId) list = list.filter((b) => b.authorId === q.authorId)
  if (q.publisherId) list = list.filter((b) => b.publisherId === q.publisherId)
  if (q.category) list = list.filter((b) => b.category === q.category)
  if (q.dateStart && q.dateEnd) {
    list = list.filter((b) => b.publishDate >= q.dateStart && b.publishDate <= q.dateEnd)
  }
  list.sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  return paginate(list.map(withRefs), q)
}

export async function createBook(payload) {
  await delay()
  const now = new Date()
  const book = {
    id: `b${Date.now()}`,
    intro: '',
    ...pickBookFields(payload_guard(arguments[0])),
    cover: { color: COVER_COLORS[(arguments[0].title.charCodeAt(0) || 0) % COVER_COLORS.length] },
    createdAt: fmtDateTime(now),
  }
  db.books.unshift(book)
  save()
  return withRefs(book)
}

function payload_guard(p) {
  return p || {}
}

function pickBookFields(p) {
  return {
    title: p.title,
    authorId: p.authorId,
    publisherId: p.publisherId,
    isbn: p.isbn,
    category: p.category,
    publishDate: p.publishDate,
    stock: p.stock ?? 0,
    intro: p.intro || '',
  }
}

export async function updateBook(id, payload) {
  await delay()
  const idx = db.books.findIndex((b) => b.id === id)
  if (idx === -1) throw new Error('图书不存在')
  db.books[idx] = { ...db.books[idx], ...pickBookFields(payload) }
  save()
  return withRefs(db.books[idx])
}

export async function deleteBook(id) {
  await delay()
  db.books = db.books.filter((b) => b.id !== id)
  save()
}

/* ---------------- 作者 ---------------- */

export async function getAuthors(q = {}) {
  await delay()
  let list = [...db.authors]
  if (q.keyword) list = list.filter((a) => a.name.toLowerCase().includes(q.keyword.toLowerCase()))
  if (q.country) list = list.filter((a) => a.country === q.country)
  list = list.map((a) => ({
    ...a,
    worksCount: db.books.filter((b) => b.authorId === a.id).length,
    color: avatarColor(a.name),
  }))
  list.sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  return paginate(list, q)
}

export async function createAuthor(payload) {
  await delay()
  const author = {
    id: `a${Date.now()}`,
    name: payload.name,
    country: payload.country || '',
    birthYear: payload.birthYear || null,
    masterpiece: payload.masterpiece || '',
    createdAt: fmtDateTime(new Date()),
  }
  db.authors.unshift(author)
  save()
  return author
}

export async function updateAuthor(id, payload) {
  await delay()
  const idx = db.authors.findIndex((a) => a.id === id)
  if (idx === -1) throw new Error('作者不存在')
  db.authors[idx] = {
    ...db.authors[idx],
    name: payload.name,
    country: payload.country || '',
    birthYear: payload.birthYear || null,
    masterpiece: payload.masterpiece || '',
  }
  save()
  return db.authors[idx]
}

export async function deleteAuthor(id) {
  await delay()
  const count = db.books.filter((b) => b.authorId === id).length
  if (count > 0) throw new Error(`该作者名下存在 ${count} 本图书，无法删除`)
  db.authors = db.authors.filter((a) => a.id !== id)
  save()
}

/* ---------------- 出版社 ---------------- */

export async function getPublishers(q = {}) {
  await delay()
  let list = [...db.publishers]
  if (q.keyword) list = list.filter((p) => p.name.toLowerCase().includes(q.keyword.toLowerCase()))
  if (q.city) list = list.filter((p) => p.city === q.city)
  list = list.map((p) => ({
    ...p,
    bookCount: db.books.filter((b) => b.publisherId === p.id).length,
  }))
  list.sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  return paginate(list, q)
}

export async function createPublisher(payload) {
  await delay()
  const publisher = {
    id: `p${Date.now()}`,
    name: payload.name,
    city: payload.city || '',
    foundedYear: payload.foundedYear || null,
    phone: payload.phone || '',
    createdAt: fmtDateTime(new Date()),
  }
  db.publishers.unshift(publisher)
  save()
  return publisher
}

export async function updatePublisher(id, payload) {
  await delay()
  const idx = db.publishers.findIndex((p) => p.id === id)
  if (idx === -1) throw new Error('出版社不存在')
  db.publishers[idx] = {
    ...db.publishers[idx],
    name: payload.name,
    city: payload.city || '',
    foundedYear: payload.foundedYear || null,
    phone: payload.phone || '',
  }
  save()
  return db.publishers[idx]
}

export async function deletePublisher(id) {
  await delay()
  const count = db.books.filter((b) => b.publisherId === id).length
  if (count > 0) throw new Error(`该出版社名下存在 ${count} 本图书，无法删除`)
  db.publishers = db.publishers.filter((p) => p.id !== id)
  save()
}

/* ---------------- Dashboard ---------------- */

export async function getDashboard() {
  await delay()
  const now = new Date()

  const monthKeys = []
  for (let i = 11; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    monthKeys.push(`${d.getFullYear()}-${pad(d.getMonth() + 1)}`)
  }
  const countIn = (list, m) => list.filter((x) => x.createdAt.startsWith(m)).length
  const trendCalc = (list) => {
    const cur = countIn(list, monthKeys[11])
    const prev = countIn(list, monthKeys[10])
    return prev === 0 ? (cur > 0 ? 100 : 0) : Math.round(((cur - prev) / prev) * 100)
  }

  const todayKey = fmtDate(now)
  const summary = {
    bookCount: db.books.length,
    authorCount: db.authors.length,
    publisherCount: db.publishers.length,
    todayCount: db.books.filter((b) => b.createdAt.startsWith(todayKey)).length,
    bookTrend: trendCalc(db.books),
    authorTrend: trendCalc(db.authors),
    publisherTrend: trendCalc(db.publishers),
    todayTrend: 12,
  }

  const trend = monthKeys.map((m) => ({ month: m.slice(2), count: countIn(db.books, m) }))

  const categoryDist = CATEGORIES.map((c) => ({
    name: c,
    value: db.books.filter((b) => b.category === c).length,
  })).filter((x) => x.value > 0)

  const topPublishers = db.publishers
    .map((p) => ({ name: p.name, value: db.books.filter((b) => b.publisherId === p.id).length }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6)

  const latest = [...db.books]
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    .slice(0, 6)
    .map(withRefs)

  return { summary, trend, categoryDist, topPublishers, latest }
}
