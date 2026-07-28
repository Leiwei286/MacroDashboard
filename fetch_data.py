"""配置驱动的数据抓取与静态 JSON 导出程序。"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from config import INDICATORS


def fetch_series(series_id: str, source: dict[str, Any]) -> pd.DataFrame:
    """按配置动态调用数据提供方，并返回 date + value 的规范化序列。"""
    provider = importlib.import_module(source["provider"])
    function = getattr(provider, source["function"])
    attempts = source.get("retries", 1)
    raw = pd.DataFrame()
    for attempt in range(1, attempts + 1):
        raw = function(**source.get("params", {}))
        if not raw.empty:
            break
        if attempt < attempts:
            delay = source.get("retry_delay_seconds", 5) * attempt
            print(f"{series_id}: 未获得数据，第 {attempt}/{attempts} 次重试将在 {delay} 秒后执行")
            time.sleep(delay)
    if raw.empty:
        raise ValueError(f"{series_id}: 数据提供方在 {attempts} 次尝试后仍未返回数据")

    # yfinance 的 download 在部分版本中即使只请求一个 ticker 也会返回 MultiIndex 列。
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw.reset_index()
    required = [source["date_column"], source["value_column"]]
    missing = set(required) - set(raw.columns)
    if missing:
        raise ValueError(f"{series_id}: 数据提供方返回缺少列 {sorted(missing)}；实际列：{list(raw.columns)}")

    result = raw[required].copy()
    result.columns = ["date", series_id]
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    result[series_id] = pd.to_numeric(result[series_id], errors="coerce")
    return result.dropna().drop_duplicates(subset="date", keep="last").sort_values("date")


def restrict_history(frame: pd.DataFrame, years: int) -> pd.DataFrame:
    """保留截至今日最近 N 个自然年的日度交易日数据。"""
    if years < 1:
        raise ValueError("history_years 必须为大于 0 的整数")
    dates = pd.to_datetime(frame["date"], errors="coerce")
    start = pd.Timestamp.today().normalize() - pd.DateOffset(years=years)
    return frame.loc[dates >= start].copy()


def calculate_indicator(indicator_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    frames = [fetch_series(series_id, source) for series_id, source in spec["series"].items()]
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="date", how="inner")

    # formula 的变量名由 series 的 key 提供；仅使用空内建环境进行计算。
    merged["value"] = eval(spec["formula"], {"__builtins__": {}}, {
        key: merged[key] for key in spec["series"]
    })
    merged = merged.replace([math.inf, -math.inf], pd.NA).dropna(subset=["value"])
    merged = restrict_history(merged, spec.get("history_years", 5))
    if merged.empty:
        raise ValueError(f"{indicator_id}: 对齐和清洗后没有可用数据")

    points = []
    series_keys = list(spec["series"])
    for row in merged.itertuples(index=False):
        item = {"date": row.date, "value": round(float(row.value), 4)}
        for key in series_keys:
            item[key] = round(float(getattr(row, key)), 4)
        points.append(item)

    latest = points[-1]
    return {
        "meta": {
            "id": indicator_id,
            "name": spec["name"],
            "description": spec["description"],
            "chart_type": spec["chart_type"],
            "frequency": spec.get("frequency", "daily"),
            "history_years": spec.get("history_years", 5),
            "unit": spec["unit"],
            "formula": spec["formula"],
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "Yahoo Finance / COMEX futures",
        },
        "latest": latest,
        "data": points,
    }


def save_json(path_text: str, payload: dict[str, Any]) -> None:
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {path}（{len(payload['data'])} 个数据点）")


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取并导出宏观指标数据")
    parser.add_argument("--indicator", choices=INDICATORS, help="仅更新指定指标")
    args = parser.parse_args()
    selected = {args.indicator: INDICATORS[args.indicator]} if args.indicator else INDICATORS

    for indicator_id, spec in selected.items():
        save_json(spec["output_file"], calculate_indicator(indicator_id, spec))


if __name__ == "__main__":
    main()
