"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.seed import SEED_ROWS

# 概览看板里模块的展示顺序、中文名、路由入口与「最近记录时间」取值字段，
# 必须与前端左侧导航（App.vue 的 navItems / router）一一对应。
MODULE_META: list[dict[str, str]] = [
    {"key": "plank", "name": "厂站信息", "path": "/plank", "time_field": "投运日期"},
    {"key": "inflow", "name": "进水监控", "path": "/inflow", "time_field": "监测时间"},
    {"key": "aeration", "name": "曝气控制", "path": "/aeration", "time_field": ""},
    {"key": "chemical", "name": "加药管理", "path": "/chemical", "time_field": ""},
    {"key": "sediment", "name": "沉淀池管理", "path": "/sediment", "time_field": ""},
    {"key": "sludge", "name": "污泥脱水", "path": "/sludge", "time_field": ""},
    {"key": "effluent", "name": "出水监测", "path": "/effluent", "time_field": "监测时间"},
    {"key": "labtest", "name": "化验分析", "path": "/labtest", "time_field": "取样日期"},
    {"key": "reagent", "name": "化验药剂", "path": "/reagent", "time_field": ""},
    {"key": "equip", "name": "设备维保", "path": "/equip", "time_field": "完成日期"},
    {"key": "pump", "name": "泵站运行", "path": "/pump", "time_field": ""},
    {"key": "power", "name": "能耗管理", "path": "/power", "time_field": ""},
    {"key": "pipe", "name": "管网巡查", "path": "/pipe", "time_field": "巡查日期"},
    {"key": "lift", "name": "提升泵站", "path": "/lift", "time_field": ""},
    {"key": "meter", "name": "仪表校准", "path": "/meter", "time_field": ""},
    {"key": "dispatch2", "name": "水量调度", "path": "/dispatch2", "time_field": "调度时段"},
    {"key": "storm", "name": "雨污调控", "path": "/storm", "time_field": "调控时段"},
    {"key": "pollutant", "name": "污染源溯源", "path": "/pollutant", "time_field": ""},
    {"key": "material", "name": "药剂耗材", "path": "/material", "time_field": ""},
    {"key": "license", "name": "排污许可", "path": "/license", "time_field": ""},
]

# 统计区间标识 -> 往前回看的天数；None 表示不限制区间。
RANGE_DAYS: dict[str, int | None] = {
    "today": 0,
    "7d": 6,
    "30d": 29,
    "all": None,
}
DEFAULT_RANGE = "today"


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }
        self._meta = {item["key"]: item for item in MODULE_META}

    def module_names(self) -> list[str]:
        """按左侧导航的顺序返回模块；导航之外若多出表，也追加在末尾。"""
        names = [item["key"] for item in MODULE_META if item["key"] in self._tables]
        names.extend(sorted(name for name in self._tables if name not in self._meta))
        return names

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def _record_date(self, module: str, row: dict[str, Any], index: int) -> date:
        """取一条记录的业务时间。

        有日期字段的模块直接读字段值（如监测时间、巡查日期）；种子数据里
        没有日期字段的模块（曝气、加药等）按记录序号补一个最近的示例时间，
        保证切换统计区间时看板有变化可看——真实项目里这个时间来自入库时间戳。
        """
        field = self._meta.get(module, {}).get("time_field", "")
        raw = str(row.get(field, "") or "") if field else ""
        parsed = self._parse_date(raw)
        if parsed is not None:
            return parsed
        return date.today() - timedelta(days=index % 3)

    @staticmethod
    def _parse_date(raw: str) -> date | None:
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None

    def overview(self, range_key: str = DEFAULT_RANGE) -> dict[str, object]:
        """汇总各模块在指定统计区间内的新增、待处理与异常量。

        待处理/异常量只统计区间内有记录的条目：切换区间后，积压的排序会跟着变。
        某个模块在区间内（或整体）没有记录时，has_data 为 False，由前端展示
        「暂无…」说明，而不是把空模块一律显示成 0。
        """
        resolved = range_key if range_key in RANGE_DAYS else DEFAULT_RANGE
        days = RANGE_DAYS[resolved]
        today = date.today()
        start = today - timedelta(days=days) if days is not None else None

        modules: list[dict[str, object]] = []
        for name in self.module_names():
            meta = self._meta.get(name, {"name": name, "path": f"/{name}"})
            rows = self.rows(name)
            latest_all: date | None = None
            scoped: list[dict[str, Any]] = []
            for index, row in enumerate(rows):
                recorded = self._record_date(name, row, index)
                latest_all = recorded if latest_all is None else max(latest_all, recorded)
                if start is None or recorded >= start:
                    scoped.append(row)
            has_data = len(rows) > 0
            modules.append({
                "key": name,
                "name": meta["name"],
                "path": meta["path"],
                "created": len(scoped),
                "pending": sum(1 for row in scoped if row.get("pending")),
                "abnormal": sum(1 for row in scoped if row.get("abnormal")),
                "latest_record": latest_all.isoformat() if latest_all else None,
                "has_data": has_data,
            })
        cards = [
            {"key": "modules", "label": "业务模块", "value": len(modules)},
            {"key": "created", "label": "今日新增" if range_key == "today" else "区间新增",
             "value": sum(int(item["created"]) for item in modules)},
            {"key": "pending", "label": "待处理",
             "value": sum(int(item["pending"]) for item in modules)},
            {"key": "abnormal", "label": "异常量",
             "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {
            "range": resolved,
            "ranges": [
                {"key": "today", "label": "今日"},
                {"key": "7d", "label": "近7日"},
                {"key": "30d", "label": "近30日"},
                {"key": "all", "label": "全部"},
            ],
            "cards": cards,
            "modules": modules,
        }


store = Store()
