<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>图书管理</h1>
        <div class="desc">共 {{ total }} 本图书</div>
      </div>
      <el-button type="primary" :icon="Plus" @click="onCreate">新增图书</el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="card filter-card">
      <el-input
        v-model="query.keyword"
        placeholder="搜索书名 / ISBN"
        :prefix-icon="Search"
        clearable
        style="width: 240px"
        @input="onSearchInput"
      />
      <el-select
        v-model="query.authorId"
        placeholder="作者"
        clearable
        filterable
        remote
        :remote-method="searchAuthors"
        style="width: 150px"
        @change="load(1)"
        @focus="searchAuthors('')"
      >
        <el-option v-for="a in authorOptions" :key="a.id" :label="a.name" :value="a.id" />
      </el-select>
      <el-select
        v-model="query.publisherId"
        placeholder="出版社"
        clearable
        filterable
        remote
        :remote-method="searchPublishers"
        style="width: 180px"
        @change="load(1)"
        @focus="searchPublishers('')"
      >
        <el-option v-for="p in publisherOptions" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select
        v-model="query.category"
        placeholder="分类"
        clearable
        style="width: 120px"
        @change="load(1)"
      >
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-date-picker
        v-model="query.dateRange"
        type="daterange"
        value-format="YYYY-MM-DD"
        start-placeholder="出版开始"
        end-placeholder="出版结束"
        style="width: 250px"
        @change="load(1)"
      />
      <el-button type="primary" @click="load(1)">查询</el-button>
      <el-button text @click="reset">重置</el-button>
    </div>

    <!-- 表格 -->
    <div class="card table-card">
      <div class="table-wrap">
        <el-table :data="list" v-loading="loading" row-key="id">
          <el-table-column label="封面" width="70">
            <template #default="{ row }">
              <div v-if="row.cover.image" class="book-cover-img">
                <img :src="row.cover.image" alt="" />
              </div>
              <div v-else class="book-cover" :style="{ background: row.cover.color }">
                {{ row.title[0] }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="书名" min-width="170" show-overflow-tooltip class-name="col-title">
            <template #default="{ row }">
              <span class="col-title-text">{{ row.title }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="isbn" label="ISBN" width="140" class-name="num" />
          <el-table-column prop="authorName" label="作者" width="110" />
          <el-table-column prop="publisherName" label="出版社" min-width="150" show-overflow-tooltip />
          <el-table-column label="分类" width="90">
            <template #default="{ row }">
              <el-tag effect="light">{{ row.category }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="库存" width="90" align="right">
            <template #default="{ row }">
              <span
                class="num"
                :style="row.stock < 5 ? 'color: var(--color-danger); font-weight: 600' : ''"
              >
                {{ row.stock }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="publishDate" label="出版日期" width="110" />
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button link type="success" :disabled="row.stock <= 0" @click="onBorrow(row)">
                借阅
              </el-button>
              <el-button link type="primary" @click="onEdit(row)">编辑</el-button>
              <el-button link @click="openDetail(row)">详情</el-button>
              <el-popconfirm
                v-if="app.isAdmin"
                title="确定删除该图书吗？"
                confirm-button-type="danger"
                @confirm="onDelete(row)"
              >
                <template #reference>
                  <el-button link type="danger">删除</el-button>
                </template>
              </el-popconfirm>
              <el-button v-else link type="danger" @click="warnNotAdmin">删除</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty description="暂无图书，点击右上角新增" />
          </template>
        </el-table>
      </div>
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @current-change="load()"
        @size-change="load(1)"
      />
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.isEdit ? '编辑图书' : '新增图书'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="书名" prop="title">
          <el-input v-model="form.title" placeholder="请输入书名" maxlength="100" />
        </el-form-item>
        <el-form-item label="作者" prop="authorId">
          <el-select
            v-model="form.authorId"
            placeholder="搜索并选择作者"
            filterable
            remote
            :remote-method="searchAuthors"
            style="width: 100%"
            @focus="searchAuthors('')"
          >
            <el-option v-for="a in authorOptions" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="出版社" prop="publisherId">
          <el-select
            v-model="form.publisherId"
            placeholder="搜索并选择出版社"
            filterable
            remote
            :remote-method="searchPublishers"
            style="width: 100%"
            @focus="searchPublishers('')"
          >
            <el-option v-for="p in publisherOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="ISBN" prop="isbn">
          <el-input v-model="form.isbn" placeholder="10 或 13 位数字" maxlength="13" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="出版日期" prop="publishDate">
          <el-date-picker
            v-model="form.publishDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
            :disabled-date="(d) => d.getTime() > Date.now()"
          />
        </el-form-item>
        <el-form-item label="封面上传">
          <div class="cover-upload">
            <div class="cover-upload-preview">
              <img v-if="form.coverImage" :src="form.coverImage" alt="" />
              <span v-else>暂无封面</span>
            </div>
            <div class="cover-upload-actions">
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                accept="image/png,image/jpeg,image/webp"
                :on-change="onCoverChange"
              >
                <el-button :icon="Upload">选择图片</el-button>
              </el-upload>
              <el-button v-if="form.coverImage" text type="danger" @click="form.coverImage = ''">
                移除封面
              </el-button>
              <div class="cover-tip">支持 JPG / PNG / WEBP，不超过 1MB</div>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="库存" prop="stock">
          <el-input-number v-model="form.stock" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="简介" prop="intro">
          <el-input
            v-model="form.intro"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="选填"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer.visible" title="图书详情" size="480px">
      <template v-if="drawer.data">
        <div class="detail-head">
          <div v-if="drawer.data.cover.image" class="book-cover-img big">
            <img :src="drawer.data.cover.image" alt="" />
          </div>
          <div v-else class="book-cover big" :style="{ background: drawer.data.cover.color }">
            {{ drawer.data.title[0] }}
          </div>
          <div>
            <h3>{{ drawer.data.title }}</h3>
            <p>{{ drawer.data.authorName }} · {{ drawer.data.publisherName }}</p>
            <el-tag size="small" effect="light">{{ drawer.data.category }}</el-tag>
          </div>
        </div>
        <el-descriptions :column="1" border style="margin-top: 16px">
          <el-descriptions-item label="ISBN">{{ drawer.data.isbn }}</el-descriptions-item>
          <el-descriptions-item label="出版日期">{{ drawer.data.publishDate }}</el-descriptions-item>
          <el-descriptions-item label="库存">{{ drawer.data.stock }} 本</el-descriptions-item>
          <el-descriptions-item label="入库时间">{{ drawer.data.createdAt }}</el-descriptions-item>
        </el-descriptions>
        <p class="intro">{{ drawer.data.intro }}</p>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Upload } from '@element-plus/icons-vue'
import {
  getBooks,
  createBook,
  updateBook,
  deleteBook,
  borrowBook,
  getAuthorOptions,
  getPublisherOptions,
  getCategories,
} from '../../api/index'
import { useAppStore } from '../../stores/app'

const app = useAppStore()

const query = reactive({
  keyword: '',
  authorId: null,
  publisherId: null,
  category: null,
  dateRange: [],
  page: 1,
  pageSize: 10,
})
const list = ref([])
const total = ref(0)
const loading = ref(false)
const categories = ref([])

async function load(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await getBooks({
      keyword: query.keyword,
      authorId: query.authorId,
      publisherId: query.publisherId,
      category: query.category,
      dateStart: query.dateRange?.[0],
      dateEnd: query.dateRange?.[1],
      page: query.page,
      pageSize: query.pageSize,
    })
    list.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}

let timer = null
function onSearchInput() {
  clearTimeout(timer)
  timer = setTimeout(() => load(1), 300)
}

function reset() {
  Object.assign(query, {
    keyword: '',
    authorId: null,
    publisherId: null,
    category: null,
    dateRange: [],
    page: 1,
  })
  load()
}

/* 远程下拉选项 */
const authorOptions = ref([])
const publisherOptions = ref([])

async function searchAuthors(kw = '') {
  authorOptions.value = await getAuthorOptions(kw)
}

async function searchPublishers(kw = '') {
  publisherOptions.value = await getPublisherOptions(kw)
}

function ensureOptions(row) {
  if (row.authorId && !authorOptions.value.some((o) => o.id === row.authorId)) {
    authorOptions.value.push({ id: row.authorId, name: row.authorName })
  }
  if (row.publisherId && !publisherOptions.value.some((o) => o.id === row.publisherId)) {
    publisherOptions.value.push({ id: row.publisherId, name: row.publisherName })
  }
}

/* 新增 / 编辑弹窗 */
const dialog = reactive({ visible: false, isEdit: false, saving: false })
const formRef = ref(null)
const emptyForm = {
  id: null,
  title: '',
  authorId: null,
  publisherId: null,
  isbn: '',
  category: null,
  publishDate: '',
  stock: 1,
  intro: '',
  coverImage: '',
}
const form = reactive({ ...emptyForm })

const rules = {
  title: [
    { required: true, message: '请输入书名', trigger: 'blur' },
    { max: 100, message: '不超过 100 字', trigger: 'blur' },
  ],
  authorId: [{ required: true, message: '请选择作者', trigger: 'change' }],
  publisherId: [{ required: true, message: '请选择出版社', trigger: 'change' }],
  isbn: [
    { required: true, message: '请输入 ISBN', trigger: 'blur' },
    { pattern: /^(\d{10}|\d{13})$/, message: 'ISBN 需为 10 或 13 位数字', trigger: 'blur' },
  ],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  publishDate: [{ required: true, message: '请选择出版日期', trigger: 'change' }],
  stock: [{ required: true, message: '请输入库存', trigger: 'blur' }],
}

function warnNotAdmin() {
  ElMessageBox.alert('不是管理员，无法操作', '权限不足', {
    confirmButtonText: '知道了',
    type: 'warning',
  })
}

function onCreate() {
  if (!app.isAdmin) return warnNotAdmin()
  openCreate()
}

function onEdit(row) {
  if (!app.isAdmin) return warnNotAdmin()
  openEdit(row)
}

function openCreate() {
  Object.assign(form, emptyForm)
  dialog.isEdit = false
  dialog.visible = true
  formRef.value?.clearValidate()
}

function openEdit(row) {
  ensureOptions(row)
  Object.assign(form, {
    id: row.id,
    title: row.title,
    authorId: row.authorId,
    publisherId: row.publisherId,
    isbn: row.isbn,
    category: row.category,
    publishDate: row.publishDate,
    stock: row.stock,
    intro: row.intro,
    coverImage: row.cover?.image || '',
  })
  dialog.isEdit = true
  dialog.visible = true
  formRef.value?.clearValidate()
}

/* 封面图片上传：本地转 Base64 随表单提交 */
function onCoverChange(file) {
  const raw = file.raw
  if (!raw) return
  if (!/^image\/(png|jpeg|webp)$/.test(raw.type)) {
    ElMessage.error('仅支持 JPG / PNG / WEBP 格式')
    return
  }
  if (raw.size > 1024 * 1024) {
    ElMessage.error('图片大小不能超过 1MB')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    form.coverImage = reader.result
  }
  reader.readAsDataURL(raw)
}

async function save() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  dialog.saving = true
  try {
    const payload = {
      title: form.title,
      authorId: form.authorId,
      publisherId: form.publisherId,
      isbn: form.isbn,
      category: form.category,
      publishDate: form.publishDate,
      stock: form.stock,
      intro: form.intro,
      coverImage: form.coverImage,
    }
    if (dialog.isEdit) {
      await updateBook(form.id, payload)
    } else {
      await createBook(payload)
    }
    ElMessage.success('保存成功')
    dialog.visible = false
    load()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row) {
  await deleteBook(row.id)
  ElMessage.success('删除成功')
  if (list.value.length === 1 && query.page > 1) query.page--
  load()
}

/* 借阅 */
async function onBorrow(row) {
  try {
    await ElMessageBox.confirm(`确定借阅《${row.title}》吗？`, '借阅确认', {
      confirmButtonText: '确定借阅',
      cancelButtonText: '取消',
      type: 'info',
    })
  } catch {
    return
  }
  try {
    const res = await borrowBook(row.id)
    ElMessage.success(`借阅成功，当前剩余库存 ${res.stock} 本`)
    load()
  } catch (e) {
    ElMessage.error(e.message || '借阅失败')
  }
}

/* 详情抽屉 */
const drawer = reactive({ visible: false, data: null })

function openDetail(row) {
  drawer.data = row
  drawer.visible = true
}

onMounted(() => {
  load()
  searchAuthors()
  searchPublishers()
  getCategories().then((c) => (categories.value = c))
})
</script>
