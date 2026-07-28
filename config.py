"""指标配置中心。

新增指标时，在 INDICATORS 中增加一条配置；抓取主程序无需改动。
数据源函数均由配置指定的数据提供方模块动态解析。
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
                "provider": "yfinance",
                "function": "download",
                "retries": 3,
                "retry_delay_seconds": 10,
                "params": {
                    "tickers": "GC=F",
                    "period": "max",
                    "interval": "1d",
                    "auto_adjust": False,
                    "progress": False,
                },
                "date_column": "Date",
                "value_column": "Close",
                "unit": "美元/金衡盎司",
            },
            "copper": {
                "name": "COMEX 铜",
                "provider": "yfinance",
                "function": "download",
                "retries": 3,
                "retry_delay_seconds": 10,
                "params": {
                    "tickers": "HG=F",
                    "period": "max",
                    "interval": "1d",
                    "auto_adjust": False,
                    "progress": False,
                },
                "date_column": "Date",
                "value_column": "Close",
                "unit": "美元/磅",
            },
        },
    },
}
