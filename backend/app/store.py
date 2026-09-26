"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.seed import SEED_ROWS

TIME_FMT = "%Y-%m-%d %H:%M"

# 概览支持的统计区间：key -> 相对今天零点的回看天数（None 表示不限制）
RANGE_DAYS: dict[str, int | None] = {
    "today": 0,
    "week": 6,
    "month": 29,
    "all": None,
}


def _seed_time(module: str, entry_id: int) -> datetime:
    """给示例数据补一条确定性的记录时间：同一模块按 id 散开，跨模块落在不同区间。

    时间相对服务启动当天生成，避免把日期写死后演示数据全部变成“历史归档”。
    """
    digest = sum(ord(ch) for ch in module)
    offset_days = (digest + entry_id * 7) % 45
    stamp = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    stamp -= timedelta(days=offset_days)
    stamp += timedelta(hours=8 + (digest + entry_id) % 10, minutes=(digest * entry_id) % 60)
    if stamp >= datetime.now():
        stamp = datetime.now() - timedelta(minutes=1)
    return stamp


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }
        for name, rows in self._tables.items():
            for row in rows:
                row.setdefault("recorded_at", _seed_time(name, int(row.get("id", 0))).strftime(TIME_FMT))

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def add_row(self, module: str, entry: dict[str, Any]) -> dict[str, Any]:
        """登记新记录时统一盖上当前时间，概览的“最近记录时间/区间新增”才有依据。"""
        entry.setdefault("recorded_at", datetime.now().strftime(TIME_FMT))
        self.rows(module).append(entry)
        return entry

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def _recorded_at(self, row: dict[str, Any]) -> datetime | None:
        raw = str(row.get("recorded_at") or "").strip()
        if not raw:
            return None
        try:
            return datetime.strptime(raw, TIME_FMT)
        except ValueError:
            return None

    def overview(self, range_key: str = "month") -> dict[str, object]:
        """运营概览：按统计区间汇总各模块的新增、待处理与异常量。

        模块统一按待处理量降序返回，前端展开任意卡片都能直接得到积压排序；
        区间内没有记录的模块各项计数为 0、最近记录时间为 None，由前端展示“暂无”。
        """
        cutoff: datetime | None = None
        days = RANGE_DAYS.get(range_key)
        if days is not None:
            cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)

        modules: list[dict[str, object]] = []
        for name in self.module_names():
            window = [
                row
                for row in self.rows(name)
                if cutoff is None or ((self._recorded_at(row) or datetime.now()) >= cutoff)
            ]
            latest = max(
                (self._recorded_at(row) for row in window),
                default=None,
            )
            modules.append({
                "key": name,
                "created": len(window),
                "pending": sum(1 for row in window if row.get("pending")),
                "abnormal": sum(1 for row in window if row.get("abnormal")),
                "latest": latest.strftime(TIME_FMT) if latest else None,
            })

        modules.sort(
            key=lambda item: (
                -int(item["pending"]),
                -int(item["abnormal"]),
                -int(item["created"]),
                str(item["key"]),
            )
        )
        cards = [
            {"key": "modules", "label": "业务模块", "value": len(modules)},
            {"key": "created", "label": "区间新增", "value": sum(int(item["created"]) for item in modules)},
            {"key": "pending", "label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"key": "abnormal", "label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"range": range_key, "cards": cards, "modules": modules}


store = Store()
