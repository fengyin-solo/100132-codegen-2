import { defineStore } from 'pinia'

import { fetchJson } from '@/api/client'

export type RangeKey = 'today' | '7d' | '30d' | 'all'

export type OverviewCard = { key: string; label: string; value: number }

export type ModuleStat = {
  key: string
  name: string
  path: string
  created: number
  pending: number
  abnormal: number
  latest_record: string | null
  has_data: boolean
}

export type Overview = {
  range: RangeKey
  ranges: { key: RangeKey; label: string }[]
  cards: OverviewCard[]
  modules: ModuleStat[]
}

/**
 * 运营概览看板的共享状态：
 * - range / activeCard 持久化到 sessionStorage，从看板进模块再返回时，
 *   区间与展开的下钻分组不会跳回默认；
 * - overview 只在区间变化或显式 refresh 时重新拉取，返回看板看到的数字
 *   与离开时一致（模块页做了状态流转后再主动 refresh）。
 */
export const useOverviewStore = defineStore('overview', {
  state: () => ({
    range: (sessionStorage.getItem('overview.range') as RangeKey | null) ?? 'today',
    activeCard: sessionStorage.getItem('overview.activeCard') ?? '',
    overview: null as Overview | null,
    loading: false,
    error: '',
    // 记录「最近一次是否从看板下钻进模块」：只有这种路径返回看板时才重新拉取，
    // 从左侧导航进模块再回来时保留看板原样，数字不会自己跳变。
    cameFromDrill: false,
  }),
  getters: {
    modules(state): ModuleStat[] {
      return state.overview?.modules ?? []
    },
    cardValue(state) {
      return (key: string) => state.overview?.cards.find((card) => card.key === key)?.value ?? 0
    },
    /** 下钻列表：按当前卡片对应的量降序，无量时保持导航顺序，无数据模块沉底。 */
    drillRows(state): ModuleStat[] {
      const rows = [...(state.overview?.modules ?? [])]
      const metric = state.activeCard === 'abnormal'
        ? 'abnormal'
        : state.activeCard === 'created'
          ? 'created'
          : 'pending'
      return rows.sort((a, b) => {
        if (a.has_data !== b.has_data) return a.has_data ? -1 : 1
        const diff = (b[metric] as number) - (a[metric] as number)
        return diff !== 0 ? diff : 0
      })
    },
  },
  actions: {
    setRange(range: RangeKey) {
      if (range === this.range) return
      this.range = range
      sessionStorage.setItem('overview.range', range)
      void this.load()
    },
    toggleCard(key: string) {
      this.activeCard = this.activeCard === key ? '' : key
      sessionStorage.setItem('overview.activeCard', this.activeCard)
    },
    async load() {
      this.loading = true
      this.error = ''
      try {
        this.overview = await fetchJson<Overview>(`/api/overview?range=${this.range}`)
        if (this.overview.range !== this.range) {
          this.range = this.overview.range
          sessionStorage.setItem('overview.range', this.range)
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : '运营概览加载失败'
      } finally {
        this.loading = false
      }
    },
    /** 看板下钻列表里点模块入口时调用，标记本次跳转来自看板。 */
    markDrillNavigation() {
      this.cameFromDrill = true
    },
    /** 回到看板时调用：只有从下钻进入模块的路径才重新拉取，保证两侧数字对得上。 */
    syncFromDrill(): Promise<void> | undefined {
      if (!this.cameFromDrill) return undefined
      this.cameFromDrill = false
      return this.load()
    },
    /** 在模块页处理完待办后调用（动作改变了状态，看板数字需要即时更新）。 */
    refresh() {
      return this.load()
    },
  },
})
