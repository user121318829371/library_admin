<template>
  <div class="card hoverable stat-card" @click="$emit('click')">
    <div class="info">
      <div class="title">{{ title }}</div>
      <div class="value num">{{ displayValue.toLocaleString() }}</div>
      <div class="trend" :class="trend >= 0 ? 'up' : 'down'">
        <el-icon :size="12">
          <ArrowUp v-if="trend >= 0" />
          <ArrowDown v-else />
        </el-icon>
        {{ Math.abs(trend) }}%
        <span class="vs">较上月</span>
      </div>
    </div>
    <div class="icon" :style="{ background: theme.bg, color: theme.color }">
      <el-icon :size="26"><component :is="icon" /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: Number, default: 0 },
  icon: { type: String, required: true },
  theme: { type: String, default: 'primary' },
  trend: { type: Number, default: 0 },
})

defineEmits(['click'])

const THEMES = {
  primary: { color: '#4F6BFF', bg: '#EEF1FF' },
  success: { color: '#22C55E', bg: '#E9F9EF' },
  purple: { color: '#8B5CF6', bg: '#F3EFFE' },
  orange: { color: '#F97316', bg: '#FEF1E7' },
}

const theme = computed(() => THEMES[props.theme] || THEMES.primary)

/* 数字滚动动画（500ms，ease-out） */
const displayValue = ref(0)
let raf = null

watch(
  () => props.value,
  (nv, ov) => {
    cancelAnimationFrame(raf)
    const from = ov ?? 0
    const start = performance.now()
    const duration = 500
    const tick = (t) => {
      const p = Math.min(1, (t - start) / duration)
      const eased = 1 - Math.pow(1 - p, 3)
      displayValue.value = Math.round(from + (nv - from) * eased)
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
  },
  { immediate: true }
)
</script>

<style scoped>
.stat-card {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 13px;
  color: var(--gray-500);
}

.value {
  font-size: 28px;
  font-weight: 600;
  color: var(--gray-900);
  line-height: 40px;
  margin: 4px 0;
}

.trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.trend.up {
  color: var(--color-success);
}

.trend.down {
  color: var(--color-danger);
}

.trend .vs {
  color: var(--gray-400);
}

.icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
