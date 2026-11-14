<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>出版社管理</h1>
        <div class="desc">共 {{ total }} 家出版社</div>
      </div>
      <el-button type="primary" :icon="Plus" @click="onCreate">新增出版社</el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="card filter-card">
      <el-input
        v-model="query.keyword"
        placeholder="搜索出版社名称"
        :prefix-icon="Search"
        clearable
        style="width: 220px"
        @input="onSearchInput"
      />
      <el-select
        v-model="query.city"
        placeholder="所在城市"
        clearable
        style="width: 130px"
        @change="load(1)"
      >
        <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
      </el-select>
      <el-button type="primary" @click="load(1)">查询</el-button>
      <el-button text @click="reset">重置</el-button>
    </div>

    <!-- 表格 -->
    <div class="card table-card">
      <div class="table-wrap">
        <el-table :data="list" v-loading="loading" row-key="id">
          <el-table-column label="名称" min-width="200" class-name="col-title">
            <template #default="{ row }">
              <div class="cell-flex">
                <span class="avatar pub-badge">{{ row.name[0] }}</span>
                <span class="col-title-text">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="city" label="所在城市" width="110" />
          <el-table-column prop="foundedYear" label="成立年份" width="100" class-name="num" />
          <el-table-column prop="phone" label="联系电话" width="150" class-name="num" />
          <el-table-column prop="bookCount" label="出版物数量" width="110" align="right" class-name="num" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="onEdit(row)">编辑</el-button>
              <el-button link @click="openDetail(row)">详情</el-button>
              <el-popconfirm
                v-if="app.isAdmin"
                title="确定删除该出版社吗？"
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
            <el-empty description="暂无出版社，点击右上角新增" />
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
      :title="dialog.isEdit ? '编辑出版社' : '新增出版社'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入名称" maxlength="50" />
        </el-form-item>
        <el-form-item label="所在城市" prop="city">
          <el-input v-model="form.city" placeholder="请输入城市" maxlength="20" />
        </el-form-item>
        <el-form-item label="成立年份" prop="foundedYear">
          <el-input-number v-model="form.foundedYear" :min="1800" :max="2026" style="width: 100%" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="选填" maxlength="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer.visible" :title="drawer.data?.name || '出版社详情'" size="480px">
      <template v-if="drawer.data">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="所在城市">{{ drawer.data.city || '-' }}</el-descriptions-item>
          <el-descriptions-item label="成立年份">{{ drawer.data.foundedYear || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ drawer.data.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="出版物数量">{{ drawer.data.bookCount }} 本</el-descriptions-item>
        </el-descriptions>
        <h3 class="drawer-sub">出版物（{{ drawer.books.length }}）</h3>
        <div v-for="b in drawer.books" :key="b.id" class="mini-book">
          <div class="book-cover" :style="{ background: b.cover.color }">{{ b.title[0] }}</div>
          <div class="meta">
            <div class="t">{{ b.title }}</div>
            <div class="a">{{ b.authorName }} · {{ b.publishDate }}</div>
          </div>
        </div>
        <el-empty v-if="!drawer.books.length" description="暂无出版物" :image-size="80" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getPublishers,
  createPublisher,
  updatePublisher,
  deletePublisher,
  getCities,
  getBooks,
} from '../../api/index'
import { useAppStore } from '../../stores/app'

const app = useAppStore()

const query = reactive({ keyword: '', city: null, page: 1, pageSize: 10 })
const list = ref([])
const total = ref(0)
const loading = ref(false)
const cities = ref([])

async function load(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await getPublishers({
      keyword: query.keyword,
      city: query.city,
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
  Object.assign(query, { keyword: '', city: null, page: 1 })
  load()
}

/* 新增 / 编辑弹窗 */
const dialog = reactive({ visible: false, isEdit: false, saving: false })
const formRef = ref(null)
const emptyForm = { id: null, name: '', city: '', foundedYear: null, phone: '' }
const form = reactive({ ...emptyForm })

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  phone: [{ pattern: /^[\d\-+() ]{5,20}$/, message: '电话格式不正确', trigger: 'blur' }],
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
  Object.assign(form, {
    id: row.id,
    name: row.name,
    city: row.city,
    foundedYear: row.foundedYear,
    phone: row.phone,
  })
  dialog.isEdit = true
  dialog.visible = true
  formRef.value?.clearValidate()
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
      name: form.name,
      city: form.city,
      foundedYear: form.foundedYear,
      phone: form.phone,
    }
    if (dialog.isEdit) {
      await updatePublisher(form.id, payload)
    } else {
      await createPublisher(payload)
    }
    ElMessage.success('保存成功')
    dialog.visible = false
    load()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row) {
  try {
    await deletePublisher(row.id)
    ElMessage.success('删除成功')
    if (list.value.length === 1 && query.page > 1) query.page--
    load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

/* 详情抽屉 */
const drawer = reactive({ visible: false, data: null, books: [] })

async function openDetail(row) {
  drawer.data = row
  drawer.visible = true
  const res = await getBooks({ publisherId: row.id, pageSize: 100 })
  drawer.books = res.list
}

onMounted(() => {
  load()
  getCities().then((c) => (cities.value = c))
})
</script>

<style scoped>
.pub-badge {
  background: linear-gradient(135deg, #4f6bff, #8b5cf6);
  border-radius: 8px;
}
</style>
