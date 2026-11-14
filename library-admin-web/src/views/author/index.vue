<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>作者管理</h1>
        <div class="desc">共 {{ total }} 位作者</div>
      </div>
      <el-button type="primary" :icon="Plus" @click="onCreate">新增作者</el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="card filter-card">
      <el-input
        v-model="query.keyword"
        placeholder="搜索作者姓名"
        :prefix-icon="Search"
        clearable
        style="width: 220px"
        @input="onSearchInput"
      />
      <el-select
        v-model="query.country"
        placeholder="国籍"
        clearable
        style="width: 130px"
        @change="load(1)"
      >
        <el-option v-for="c in countries" :key="c" :label="c" :value="c" />
      </el-select>
      <el-button type="primary" @click="load(1)">查询</el-button>
      <el-button text @click="reset">重置</el-button>
    </div>

    <!-- 表格 -->
    <div class="card table-card">
      <div class="table-wrap">
        <el-table :data="list" v-loading="loading" row-key="id">
          <el-table-column label="姓名" min-width="170" class-name="col-title">
            <template #default="{ row }">
              <div class="cell-flex">
                <span class="avatar" :style="{ background: row.color }">{{ row.name[0] }}</span>
                <span class="col-title-text">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="country" label="国籍" width="100" />
          <el-table-column prop="birthYear" label="出生年份" width="100" class-name="num" />
          <el-table-column prop="masterpiece" label="代表作" min-width="180" show-overflow-tooltip />
          <el-table-column prop="worksCount" label="作品数量" width="100" align="right" class-name="num" />
          <el-table-column prop="createdAt" label="创建时间" width="150" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="onEdit(row)">编辑</el-button>
              <el-button link @click="openDetail(row)">详情</el-button>
              <el-popconfirm
                v-if="app.isAdmin"
                title="确定删除该作者吗？"
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
            <el-empty description="暂无作者，点击右上角新增" />
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
      :title="dialog.isEdit ? '编辑作者' : '新增作者'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" maxlength="30" />
        </el-form-item>
        <el-form-item label="国籍" prop="country">
          <el-input v-model="form.country" placeholder="请输入国籍" maxlength="20" />
        </el-form-item>
        <el-form-item label="出生年份" prop="birthYear">
          <el-input-number v-model="form.birthYear" :min="1800" :max="2026" style="width: 100%" />
        </el-form-item>
        <el-form-item label="代表作" prop="masterpiece">
          <el-input v-model="form.masterpiece" placeholder="选填" maxlength="50" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer.visible" :title="drawer.data?.name || '作者详情'" size="480px">
      <template v-if="drawer.data">
        <div class="detail-head">
          <span class="avatar" :style="{ background: drawer.data.color, width: '56px', height: '56px', fontSize: '22px', marginRight: 0 }">
            {{ drawer.data.name[0] }}
          </span>
          <div>
            <h3>{{ drawer.data.name }}</h3>
            <p>{{ drawer.data.country }} · {{ drawer.data.birthYear || '生年不详' }}</p>
          </div>
        </div>
        <el-descriptions :column="1" border style="margin-top: 16px">
          <el-descriptions-item label="代表作">{{ drawer.data.masterpiece || '-' }}</el-descriptions-item>
          <el-descriptions-item label="作品数量">{{ drawer.data.worksCount }} 本</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ drawer.data.createdAt }}</el-descriptions-item>
        </el-descriptions>
        <h3 class="drawer-sub">TA 的作品（{{ drawer.books.length }}）</h3>
        <div v-for="b in drawer.books" :key="b.id" class="mini-book">
          <div class="book-cover" :style="{ background: b.cover.color }">{{ b.title[0] }}</div>
          <div class="meta">
            <div class="t">{{ b.title }}</div>
            <div class="a">{{ b.publisherName }} · {{ b.publishDate }}</div>
          </div>
        </div>
        <el-empty v-if="!drawer.books.length" description="暂无作品" :image-size="80" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getAuthors, createAuthor, updateAuthor, deleteAuthor, getCountries, getBooks } from '../../api/index'
import { useAppStore } from '../../stores/app'

const app = useAppStore()

const query = reactive({ keyword: '', country: null, page: 1, pageSize: 10 })
const list = ref([])
const total = ref(0)
const loading = ref(false)
const countries = ref([])

async function load(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await getAuthors({
      keyword: query.keyword,
      country: query.country,
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
  Object.assign(query, { keyword: '', country: null, page: 1 })
  load()
}

/* 新增 / 编辑弹窗 */
const dialog = reactive({ visible: false, isEdit: false, saving: false })
const formRef = ref(null)
const emptyForm = { id: null, name: '', country: '', birthYear: null, masterpiece: '' }
const form = reactive({ ...emptyForm })

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
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
    country: row.country,
    birthYear: row.birthYear,
    masterpiece: row.masterpiece,
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
      country: form.country,
      birthYear: form.birthYear,
      masterpiece: form.masterpiece,
    }
    if (dialog.isEdit) {
      await updateAuthor(form.id, payload)
    } else {
      await createAuthor(payload)
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
    await deleteAuthor(row.id)
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
  const res = await getBooks({ authorId: row.id, pageSize: 100 })
  drawer.books = res.list
}

onMounted(() => {
  load()
  getCountries().then((c) => (countries.value = c))
})
</script>
