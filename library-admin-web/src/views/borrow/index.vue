<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>图书借阅</h1>
        <div class="desc">共 {{ total }} 条借阅记录</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="card filter-card">
      <el-input
        v-model="query.keyword"
        placeholder="搜索书名 / 借阅人"
        :prefix-icon="Search"
        clearable
        style="width: 240px"
        @input="onSearchInput"
      />
      <el-select
        v-model="query.status"
        placeholder="借阅状态"
        clearable
        style="width: 140px"
        @change="load(1)"
      >
        <el-option label="借阅中" value="借阅中" />
        <el-option label="已归还" value="已归还" />
      </el-select>
      <el-button type="primary" @click="load(1)">查询</el-button>
      <el-button text @click="reset">重置</el-button>
    </div>

    <!-- 表格 -->
    <div class="card table-card">
      <div class="table-wrap">
        <el-table :data="list" v-loading="loading" row-key="id">
          <el-table-column label="书名" min-width="200" class-name="col-title">
            <template #default="{ row }">
              <div class="col-title-text book-title">{{ row.bookTitle }}</div>
              <div class="book-isbn">{{ row.bookIsbn }}</div>
            </template>
          </el-table-column>
          <el-table-column label="借阅人" width="140">
            <template #default="{ row }">
              <div class="borrower">
                <el-avatar :size="24" class="borrower-avatar">{{ row.userName[0] }}</el-avatar>
                <span>{{ row.userName }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status === '借阅中' ? 'warning' : 'success'" effect="light">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="borrowedAt" label="借出时间" width="160" />
          <el-table-column label="归还时间" width="160">
            <template #default="{ row }">{{ row.returnedAt || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === '借阅中'"
                link
                type="primary"
                @click="onReturn(row)"
              >
                归还
              </el-button>
              <span v-else class="muted">已完成</span>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty description="暂无借阅记录，可在图书管理中借阅图书" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getBorrows, returnBorrow } from '../../api/index'
import { useAppStore } from '../../stores/app'

const app = useAppStore()

const query = reactive({ keyword: '', status: null, page: 1, pageSize: 10 })
const list = ref([])
const total = ref(0)
const loading = ref(false)

async function load(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await getBorrows({
      keyword: query.keyword,
      status: query.status,
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
  Object.assign(query, { keyword: '', status: null, page: 1 })
  load()
}

async function onReturn(row) {
  if (!app.isAdmin) {
    ElMessageBox.alert('不是管理员，无法操作', '权限不足', {
      confirmButtonText: '知道了',
      type: 'warning',
    })
    return
  }
  try {
    await ElMessageBox.confirm(`确认《${row.bookTitle}》已归还吗？`, '归还确认', {
      confirmButtonText: '确认归还',
      cancelButtonText: '取消',
      type: 'info',
    })
  } catch {
    return
  }
  try {
    await returnBorrow(row.id)
    ElMessage.success('归还成功，库存已恢复')
    load()
  } catch (e) {
    ElMessage.error(e.message || '归还失败')
  }
}

onMounted(() => load())
</script>

<style scoped>
.book-title {
  font-weight: 500;
  color: var(--gray-900);
}

.book-isbn {
  font-size: 12px;
  color: var(--gray-400);
  margin-top: 2px;
}

.borrower {
  display: flex;
  align-items: center;
  gap: 8px;
}

.borrower-avatar {
  background: var(--color-primary);
  font-size: 12px;
}

.muted {
  color: var(--gray-400);
  font-size: 13px;
}
</style>
