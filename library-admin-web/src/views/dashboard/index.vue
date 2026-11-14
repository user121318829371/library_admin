<template>
  <div class="page">
    <!-- 指标卡 -->
    <div class="stat-grid">
      <StatCard
        title="图书总数"
        :value="summary.bookCount"
        icon="Reading"
        theme="primary"
        :trend="summary.bookTrend"
        @click="$router.push('/book')"
      />
      <StatCard
        title="作者总数"
        :value="summary.authorCount"
        icon="EditPen"
        theme="purple"
        :trend="summary.authorTrend"
        @click="$router.push('/author')"
      />
      <StatCard
        title="出版社总数"
        :value="summary.publisherCount"
        icon="OfficeBuilding"
        theme="success"
        :trend="summary.publisherTrend"
        @click="$router.push('/publisher')"
      />
      <StatCard
        title="今日入库"
        :value="summary.todayCount"
        icon="TrendCharts"
        theme="orange"
        :trend="summary.todayTrend"
        @click="$router.push('/book')"
      />
    </div>

    <!-- 趋势 + 分类分布 -->
    <div class="row">
      <div class="card chart-card span2">
        <div class="chart-head">
          <h2>入库趋势</h2>
          <span class="sub">近 12 个月</span>
        </div>
        <div ref="trendRef" class="chart"></div>
      </div>
      <div class="card chart-card">
        <div class="chart-head">
          <h2>图书分类分布</h2>
        </div>
        <div ref="pieRef" class="chart"></div>
      </div>
    </div>

    <!-- 每日好书推荐 + 最新入库 -->
    <div class="row row-equal">
      <div class="card chart-card">
        <div class="chart-head">
          <h2>最新入库</h2>
          <el-link type="primary" :underline="false" @click="$router.push('/book')">查看全部</el-link>
        </div>
        <div class="latest-list">
          <div v-for="b in latest" :key="b.id" class="latest-item">
            <div
              class="cover"
              :style="b.cover.image ? {} : { background: b.cover.color }"
            >
              <img v-if="b.cover.image" :src="b.cover.image" alt="" />
              <template v-else>{{ b.title[0] }}</template>
            </div>
            <div class="meta">
              <div class="t">{{ b.title }}</div>
              <div class="a">{{ b.authorName }} · {{ b.publisherName }}</div>
            </div>
            <div class="time">{{ b.createdAt.slice(0, 10) }}</div>
          </div>
        </div>
      </div>
      <div class="card chart-card">
        <div class="chart-head">
          <h2>每日好书推荐</h2>
          <span class="sub">今日摘句</span>
        </div>
        <div v-if="recommend" class="recommend">
          <div class="quote-mark">“</div>
          <p class="quote">{{ recommend.quote }}</p>
          <p class="quote-from">—— 《{{ recommend.book.title }}》</p>
        </div>
        <el-empty v-else description="暂无推荐" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import StatCard from '../../components/StatCard.vue'
import { getDashboard } from '../../api/index'

const PALETTE = ['#4F6BFF', '#22C55E', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#84CC16']
const AXIS_STYLE = {
  axisLine: { lineStyle: { color: '#E2E8F0' } },
  axisLabel: { color: '#64748B' },
  axisTick: { show: false },
}

const summary = ref({
  bookCount: 0,
  authorCount: 0,
  publisherCount: 0,
  todayCount: 0,
  bookTrend: 0,
  authorTrend: 0,
  publisherTrend: 0,
  todayTrend: 0,
})
const latest = ref([])
const recommend = ref(null)

const trendRef = ref(null)
const pieRef = ref(null)
let charts = []

/* 名著摘句库（按书名匹配，缺省回退到图书简介） */
const QUOTES = {
  活着: '人是为了活着本身而活着，而不是为了活着之外的任何事物而活着。',
  平凡的世界: '生活不能等待别人来安排，要自己去争取和奋斗。',
  百年孤独: '生命中真正重要的不是你遭遇了什么，而是你记住了哪些事，又是如何铭记的。',
  1984: '谁控制了过去，谁就控制了未来；谁控制了现在，谁就控制了过去。',
  围城: '婚姻是一座围城，城外的人想进去，城里的人想出来。',
  三体: '弱小和无知不是生存的障碍，傲慢才是。',
  挪威的森林: '死并非生的对立面，而作为生的一部分永存。',
  老人与海: '一个人可以被毁灭，但不能被打败。',
  白夜行: '我的天空里没有太阳，总是黑夜，但并不暗，因为有东西代替了太阳。',
  霍乱时期的爱情: '趁着年轻，好好利用这种狂热，尽力去爱，因为爱情本身就是一种恩赐。',
  动物农场: '所有动物一律平等，但有些动物比其他动物更加平等。',
  艺术的故事: '实际上没有艺术这种东西，只有艺术家而已。',
  失控: '未来已经到来，只是分布不均。',
  浪潮之巅: '对于一个公司来讲，最重要的是基因，而不是努力。',
  '经济学原理：微观经济学分册': '天下没有免费的午餐。',
  '明朝那些事儿（壹）': '历史没有真相，只残存一个道理。',
  许三观卖血记: '他的一生就是在卖血，卖血就是他的一生。',
  解忧杂货店: '如果自己不想积极认真地生活，不管得到什么样的回答都没用。',
}

onMounted(async () => {
  const data = await getDashboard()
  summary.value = data.summary
  latest.value = data.latest
  recommend.value = pickRecommend(data.latest)
  renderTrend(data.trend)
  renderPie(data.categoryDist)
  window.addEventListener('resize', onResize)
})

/* 每日一荐：优先在有摘句的图书中按当天日期轮换 */
function pickRecommend(books) {
  if (!books || !books.length) return null
  const now = new Date()
  const dayIndex = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000)
  const withQuote = books.filter((b) => QUOTES[b.title])
  const pool = withQuote.length ? withQuote : books
  const book = pool[dayIndex % pool.length]
  return { book, quote: QUOTES[book.title] || book.intro || `《${book.title}》馆藏好书。` }
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  charts.forEach((c) => c.dispose())
})

function onResize() {
  charts.forEach((c) => c.resize())
}

function renderTrend(trend) {
  const chart = echarts.init(trendRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 24, bottom: 28 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trend.map((t) => t.month),
      ...AXIS_STYLE,
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' } },
      axisLabel: { color: '#64748B' },
    },
    series: [
      {
        name: '入库数量',
        type: 'line',
        smooth: true,
        symbolSize: 6,
        data: trend.map((t) => t.count),
        lineStyle: { width: 3, color: '#4F6BFF' },
        itemStyle: { color: '#4F6BFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79,107,255,0.22)' },
            { offset: 1, color: 'rgba(79,107,255,0)' },
          ]),
        },
      },
    ],
  })
  charts.push(chart)
}

function renderPie(dist) {
  const chart = echarts.init(pieRef.value)
  chart.setOption({
    color: PALETTE,
    tooltip: { trigger: 'item', formatter: '{b}：{c} 本（{d}%）' },
    legend: {
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { color: '#64748B' },
    },
    series: [
      {
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['50%', '44%'],
        roseType: 'radius',
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        data: dist,
      },
    ],
  })
  charts.push(chart)
}
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 16px;
}

.row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.span2 {
  grid-column: span 2;
}

/* 等宽两栏（每日好书推荐 + 最新入库） */
.row-equal {
  grid-template-columns: repeat(2, 1fr);
}

.chart-card h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-900);
}

.chart-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.chart-head .sub {
  font-size: 12px;
  color: var(--gray-400);
}

.chart {
  height: 300px;
}

/* 最新入库列表 */
.latest-list {
  height: 300px;
  overflow-y: auto;
}

.latest-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--gray-200);
}

.latest-item:last-child {
  border-bottom: none;
}

.cover {
  width: 36px;
  height: 48px;
  border-radius: 4px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  overflow: hidden;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 每日好书推荐 */
.recommend {
  height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px 24px 40px 6px;
}

.quote-mark {
  font-size: 56px;
  line-height: 0.9;
  height: 32px;
  color: var(--color-primary);
  opacity: 0.18;
  font-family: Georgia, 'Times New Roman', serif;
}

.quote {
  font-size: 22px;
  line-height: 1.9;
  color: var(--gray-900);
  font-weight: 500;
  margin: 16px auto 0;
  max-width: 760px;
  text-align: center;
}

.quote-from {
  margin-top: 14px;
  font-size: 15px;
  color: var(--gray-800);
  text-align: right;
}

.latest-item .meta {
  flex: 1;
  min-width: 0;
}

.latest-item .t {
  color: var(--gray-900);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.latest-item .a {
  font-size: 12px;
  color: var(--gray-500);
  margin-top: 2px;
}

.latest-item .time {
  font-size: 12px;
  color: var(--gray-400);
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .row,
  .row-equal {
    grid-template-columns: 1fr;
  }
  .span2 {
    grid-column: span 1;
  }
}
</style>
