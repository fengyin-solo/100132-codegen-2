<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，点击卡片可下钻查看模块积压明细与最近记录时间。</p>
      </div>
      <div class="page-actions range-bar">
        <label class="filter-item">
          <span>统计区间</span>
          <select v-model="rangeKey" class="range-select" @change="reload">
            <option v-for="opt in rangeOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
          </select>
        </label>
      </div>
    </header>

    <div class="stat-row">
      <button
        v-for="card in cards"
        :key="card.key"
        type="button"
        class="stat-card stat-card--drill"
        :class="{ 'is-active': activeCard === card.key }"
        @click="toggleCard(card.key)"
      >
        <span class="stat-label">
          {{ card.label }}
          <em class="drill-hint">{{ activeCard === card.key ? '收起明细 ▲' : '查看明细 ▼' }}</em>
        </span>
        <strong class="stat-value">{{ card.value }}</strong>
      </button>
    </div>

    <section v-if="activeCard" class="drill-panel">
      <div class="drill-head">
        <h3>{{ activeCardLabel }} · 模块下钻</h3>
        <span class="drill-tip">按待处理量排列，模块名称后标注该模块最近一条记录的时间</span>
      </div>
      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>业务模块</th>
            <th>最近记录时间</th>
            <th :class="{ 'metric-on': activeCard === 'created' }">区间新增</th>
            <th :class="{ 'metric-on': activeCard === 'pending' }">待处理</th>
            <th :class="{ 'metric-on': activeCard === 'abnormal' }">异常量</th>
            <th>进入模块</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in moduleRows" :key="row.key">
            <td>{{ moduleMeta(row.key).label }}</td>
            <td>{{ row.latest ?? '暂无记录' }}</td>
            <td :class="{ 'metric-on': activeCard === 'created' }">{{ formatMetric(row, 'created') }}</td>
            <td :class="{ 'metric-on': activeCard === 'pending' }">{{ formatMetric(row, 'pending') }}</td>
            <td :class="{ 'metric-on': activeCard === 'abnormal' }">{{ formatMetric(row, 'abnormal') }}</td>
            <td>
              <RouterLink class="link" :to="moduleMeta(row.key).path">进入 {{ moduleMeta(row.key).label }}</RouterLink>
            </td>
          </tr>
          <tr v-if="!moduleRows.length">
            <td colspan="6" class="empty-state">{{ currentRange.label }}暂无可统计的业务模块</td>
          </tr>
        </tbody>
      </table>
      <p v-if="activeCard !== 'modules' && activeMetricRows.length === 0" class="empty-state drill-empty">
        {{ currentRange.label }}内没有「{{ activeCardLabel }}」记录
      </p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'
import { moduleMeta } from '@/modules'

type MetricKey = 'created' | 'pending' | 'abnormal'
type CardKey = 'modules' | MetricKey

type Overview = {
  range: string
  cards: { key: CardKey; label: string; value: number }[]
  modules: {
    key: string
    created: number
    pending: number
    abnormal: number
    latest: string | null
  }[]
}

const rangeOptions = [
  { key: 'today', label: '今日' },
  { key: 'week', label: '近7天' },
  { key: 'month', label: '近30天' },
  { key: 'all', label: '全部' },
] as const

const RANGE_STORAGE_KEY = 'dashboard.range'
const CARD_STORAGE_KEY = 'dashboard.activeCard'

function persistedRange(): string {
  const saved = localStorage.getItem(RANGE_STORAGE_KEY)
  return rangeOptions.some((opt) => opt.key === saved) ? saved! : 'month'
}

function persistedCard(): CardKey | null {
  const saved = localStorage.getItem(CARD_STORAGE_KEY) as CardKey | null
  return saved && ['modules', 'created', 'pending', 'abnormal'].includes(saved) ? saved : null
}

// 区间与展开的卡片都跨页面停留保留：从模块返回时不会跳回默认区间/默认卡片
const rangeKey = ref<string>(persistedRange())
const activeCard = ref<CardKey | null>(persistedCard())

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])
const errorMessage = ref('')

const currentRange = computed(() => {
  const found = rangeOptions.find((opt) => opt.key === rangeKey.value)
  return found ?? rangeOptions[2]
})

const activeCardLabel = computed(
  () => cards.value.find((card) => card.key === activeCard.value)?.label ?? '',
)

const activeMetricRows = computed(() => {
  if (activeCard.value === 'modules' || activeCard.value === null) return moduleRows.value
  return moduleRows.value.filter((row) => row[activeCard.value as MetricKey] > 0)
})

// 模块在区间内没有记录时指标展示“暂无”，而不是一律显示成 0
function formatMetric(row: Overview['modules'][number], key: MetricKey): string | number {
  if (row.created === 0) return '暂无'
  return row[key]
}

function toggleCard(key: CardKey) {
  activeCard.value = activeCard.value === key ? null : key
  if (activeCard.value) {
    localStorage.setItem(CARD_STORAGE_KEY, activeCard.value)
  } else {
    localStorage.removeItem(CARD_STORAGE_KEY)
  }
}

async function reload() {
  errorMessage.value = ''
  localStorage.setItem(RANGE_STORAGE_KEY, rangeKey.value)
  try {
    const payload = await fetchJson<Overview>(`/api/overview?range=${rangeKey.value}`)
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '运营概览读取失败'
    cards.value = []
    moduleRows.value = []
  }
}

// 每次进入看板都重新拉取，保证从模块处理完待办返回后，卡片数字与模块现状一致
onMounted(reload)
</script>
