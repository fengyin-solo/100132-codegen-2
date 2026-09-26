/** 业务模块清单：左侧导航、运营概览下钻与路由共用同一份，保证入口对得上。 */
export interface ModuleMeta {
  key: string
  label: string
  path: string
}

export const MODULES: ModuleMeta[] = [
  { key: 'plank', label: '厂站信息', path: '/plank' },
  { key: 'inflow', label: '进水监控', path: '/inflow' },
  { key: 'aeration', label: '曝气控制', path: '/aeration' },
  { key: 'chemical', label: '加药管理', path: '/chemical' },
  { key: 'sediment', label: '沉淀池管理', path: '/sediment' },
  { key: 'sludge', label: '污泥脱水', path: '/sludge' },
  { key: 'effluent', label: '出水监测', path: '/effluent' },
  { key: 'labtest', label: '化验分析', path: '/labtest' },
  { key: 'reagent', label: '化验药剂', path: '/reagent' },
  { key: 'equip', label: '设备维保', path: '/equip' },
  { key: 'pump', label: '泵站运行', path: '/pump' },
  { key: 'power', label: '能耗管理', path: '/power' },
  { key: 'pipe', label: '管网巡查', path: '/pipe' },
  { key: 'lift', label: '提升泵站', path: '/lift' },
  { key: 'meter', label: '仪表校准', path: '/meter' },
  { key: 'dispatch2', label: '水量调度', path: '/dispatch2' },
  { key: 'storm', label: '雨污调控', path: '/storm' },
  { key: 'pollutant', label: '污染源溯源', path: '/pollutant' },
  { key: 'material', label: '药剂耗材', path: '/material' },
  { key: 'license', label: '排污许可', path: '/license' },
]

export const MODULE_MAP: Record<string, ModuleMeta> = Object.fromEntries(
  MODULES.map((item) => [item.key, item]),
)

export function moduleMeta(key: string): ModuleMeta {
  return MODULE_MAP[key] ?? { key, label: key, path: `/${key}` }
}
