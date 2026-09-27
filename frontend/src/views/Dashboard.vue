<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，点开卡片可下钻查看各模块积压，先看总量再看异常。</p>
      </div>
      <div class="range-switch" role="group" aria-label="统计区间">
        <button
          v-for="item in ranges"
          :key="item.key"
          type="button"
          class="btn"
          :class="{ primary: item.key === store.range }"
          @click="store.setRange(item.key)"
        >
          {{ item.label }}
        </button>
      </div>
    </header>

    <p v-if="store.error" class="error-text">{{ store.error }}</p>

    <div class="stat-row">
      <article
        v-for="card in cards"
        :key="card.key"
        class="stat-card"
        :class="{
          'stat-card--clickable': card.key !== 'modules',
          'stat-card--active': store.activeCard === card.key,
        }"
        :role="card.key === 'modules' ? undefined : 'button'"
        :tabindex="card.key === 'modules' ? undefined : 0"
        @click="toggleCard(card)"
        @keydown.enter="toggleCard(card)"
        @keydown.space.prevent="toggleCard(card)"
      >
        <span class="stat-label">
          {{ card.label }}
          <span v-if="card.key !== 'modules'" class="stat-hint">
            {{ store.activeCard === card.key ? '点击收起' : '点击下钻' }}
          </span>
        </span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>

    <transition name="drill">
      <section v-if="activeMetric" class="drill-panel">
        <header class="drill-head">
          <h3>{{ activeCardLabel }} · 模块下钻</h3>
          <span class="page-desc">按{{ activeCardLabel }}从高到低排列，点击模块名进入对应业务处理。</span>
        </header>
        <table class="data-table">
          <thead>
            <tr>
              <th>业务模块</th>
              <th>最近记录</th>
              <th>待处理</th>
              <th>异常量</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in store.drillRows" :key="row.key">
              <td>
                <RouterLink class="link" :to="row.path" @click="store.markDrillNavigation()">{{ row.name }}</RouterLink>
              </td>
              <td class="muted-cell">{{ row.latest_record ?? '暂无记录时间' }}</td>
              <template v-if="row.has_data">
                <td>
                  <span v-if="row.pending > 0" class="badge badge--pending">{{ row.pending }}</span>
                  <span v-else class="muted-cell">0</span>
                </td>
                <td>
                  <span v-if="row.abnormal > 0" class="badge badge--abnormal">{{ row.abnormal }}</span>
                  <span v-else class="muted-cell">0</span>
                </td>
              </template>
              <template v-else>
                <td><span class="muted-cell">暂无待处理记录</span></td>
                <td><span class="muted-cell">暂无异常记录</span></td>
              </template>
              <td>
                <RouterLink class="link" :to="row.path" @click="store.markDrillNavigation()">进入模块 →</RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="store.loading" class="page-desc drill-loading">数据刷新中…</p>
      </section>
    </transition>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import { useOverviewStore, type OverviewCard, type RangeKey } from '@/stores/overview'

const store = useOverviewStore()
const { overview } = storeToRefs(store)

const FALLBACK_RANGES: { key: RangeKey; label: string }[] = [
  { key: 'today', label: '今日' },
  { key: '7d', label: '近7日' },
  { key: '30d', label: '近30日' },
  { key: 'all', label: '全部' },
]

const ranges = computed(() => overview.value?.ranges ?? FALLBACK_RANGES)

const cards = computed(() => overview.value?.cards ?? [
  { key: 'modules', label: '业务模块', value: 0 },
  { key: 'created', label: '今日新增', value: 0 },
  { key: 'pending', label: '待处理', value: 0 },
  { key: 'abnormal', label: '异常量', value: 0 },
])

const activeMetric = computed<'created' | 'pending' | 'abnormal' | null>(() => {
  const key = store.activeCard
  if (key === 'abnormal' || key === 'created' || key === 'pending') return key
  return null
})

const activeCardLabel = computed(() => {
  return cards.value.find((item) => item.key === store.activeCard)?.label ?? ''
})

function toggleCard(card: OverviewCard) {
  // 「业务模块」卡片是模块总数，没有可下钻的明细。
  if (card.key !== 'modules') store.toggleCard(card.key)
}

onMounted(() => {
  // 首次进入拉取；区间与展开状态由 store/sessionStorage 记住，返回本页不重置。
  // 从下钻进入模块再返回时同步一次，卡片数字与模块侧严格保持一致。
  const synced = store.syncFromDrill()
  if (!overview.value && !synced) void store.load()
})
</script>

<style scoped>
.range-switch { display: flex; gap: 6px; }
.range-switch .btn { padding: 4px 12px; font-size: 13px; }
.stat-card--clickable { cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.stat-card--clickable:hover { border-color: var(--brand); }
.stat-card--clickable:focus-visible { outline: 2px solid var(--brand); outline-offset: 1px; }
.stat-card--active { border-color: var(--brand); box-shadow: 0 0 0 1px var(--brand) inset; }
.stat-hint { float: right; font-weight: 400; color: #94a3b8; font-size: 11px; }
.drill-panel {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}
.drill-head { margin-bottom: 8px; }
.drill-head h3 { margin: 0; font-size: 15px; }
.muted-cell { color: var(--muted); }
.badge {
  display: inline-block;
  min-width: 24px;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}
.badge--pending { background: #fff4e5; color: #b54708; }
.badge--abnormal { background: #fee4e2; color: #b42318; }
.drill-loading { margin: 8px 0 0; }
.drill-enter-active, .drill-leave-active { transition: opacity 0.15s, transform 0.15s; }
.drill-enter-from, .drill-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
