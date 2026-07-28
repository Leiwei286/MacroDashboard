"""指标配置中心。

新增指标时，在 INDICATORS 中增加一条配置；抓取主程序无需改动。
数据源函数均由 akshare 模块动态解析。
"""

INDICATORS = {
    "gold_copper_ratio": {
        "name": "金铜比",
        "description": "COMEX 黄金主连收盘价 / COMEX 铜主连收盘价",
        "chart_type": "line",
        "frequency": "daily",
        "history_years": 20,
        "unit": "倍",
        "output_file": "docs/data/gold_copper_ratio.json",
        "formula": "gold / copper",
        "series": {
            "gold": {
                "name": "COMEX 黄金",
                "akshare_function": "futures_global_hist_em",
                "params": {"symbol": "GC00Y"},
                "date_column": "日期",
                "value_column": "最新价",
                "unit": "美元/金衡盎司",
            },
            "copper": {
                "name": "COMEX 铜",
                "akshare_function": "futures_global_hist_em",
                "params": {"symbol": "HG00Y"},
                "date_column": "日期",
                "value_column": "最新价",
                "unit": "美元/磅",
            },
        },
    },
}
