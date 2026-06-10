"""
芯片产业链财报分析模块
从东方财富财报数据提取营收、毛利、净利润、同比/环比增长
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 公司主营业务收入构成 (基于公开数据)
COMPANY_SEGMENTS = {
    "002916": {"封装基板": 0.65, "PCB": 0.30, "其他": 0.05},  # 深南电路
    "002371": {"半导体设备": 0.80, "电子元器件": 0.15, "其他": 0.05},  # 北方华创
    "002463": {"先进封装": 0.55, "传统封装": 0.35, "其他": 0.10},  # 长电科技
    "002920": {"封装测试": 0.90, "其他": 0.10},  # 通富微电
    "688981": {"晶圆代工": 0.95, "其他": 0.05},  # 中芯国际
    "603486": {"AI芯片": 0.85, "其他": 0.15},  # 寒武纪
    "603986": {"存储芯片": 0.75, "MCU": 0.20, "其他": 0.05},  #兆易创新
    "688008": {"内存接口芯片": 0.70, "津逮服务器": 0.20, "其他": 0.10},  # 澜起科技
    "600183": {"覆铜板": 0.60, "PCB": 0.35, "其他": 0.05},  # 生益科技
    "002837": {"精密温控": 0.75, "机房空调": 0.20, "其他": 0.05},  # 英维克
    "000977": {"服务器": 0.80, "存储": 0.15, "其他": 0.05},  # 浪潮信息
    "688012": {"刻蚀设备": 0.70, "MOCVD": 0.25, "其他": 0.05},  # 中微公司
    "688221": {"EDA软件": 0.85, "其他": 0.15},  # 华大九天
    "601216": {"硅材料": 0.90, "其他": 0.10},  # 沪硅产业
}


class FinancialAnalyzer:
    """财报分析器"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)

    def load_financial_data(self, date_str: str, symbol: str = None) -> Dict:
        """加载财务数据"""
        if symbol:
            file_path = self.data_dir / "financials" / date_str / f"{symbol}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        else:
            # 加载所有
            results = {}
            fin_dir = self.data_dir / "financials" / date_str
            if fin_dir.exists():
                for f in fin_dir.glob("*.json"):
                    with open(f, "r", encoding="utf-8") as file:
                        symbol_code = f.stem
                        results[symbol_code] = json.load(file)
            return results
        return {}

    def parse_financial_report(self, raw_data: dict, symbol: str) -> Optional[dict]:
        """解析财务报告数据"""
        if not raw_data or "data" not in raw_data:
            return None

        data = raw_data.get("data", {})
        reports = data.get("financialReport", []) or data.get("reports", [])

        if not reports or len(reports) == 0:
            return None

        # 取最新一期报告
        latest = reports[0] if isinstance(reports, list) else reports

        return {
            "symbol": symbol,
            "report_date": latest.get("reportDate", latest.get("report_date", "")),
            "total_revenue": self._parse_number(latest.get("totalRevenue", latest.get("total_revenue", 0))),
            "revenue_yoy": self._parse_number(latest.get("revenueYoy", latest.get("revenue_yoy", 0))),
            "net_profit": self._parse_number(latest.get("netProfit", latest.get("net_profit", 0))),
            "profit_yoy": self._parse_number(latest.get("profitYoy", latest.get("profit_yoy", 0))),
            "gross_margin": self._parse_number(latest.get("grossMargin", latest.get("gross_margin", 0))),
            "net_margin": self._parse_number(latest.get("netMargin", latest.get("net_margin", 0))),
        }

    def _parse_number(self, value) -> float:
        """解析数字"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", ""))
            except:
                return 0.0
        return 0.0

    def attribute_revenue_to_segments(self, symbol: str, total_revenue: float) -> Dict[str, float]:
        """将公司收入分解到产业链 segments"""
        composition = COMPANY_SEGMENTS.get(symbol, {"其他": 1.0})
        return {
            segment: total_revenue * ratio
            for segment, ratio in composition.items()
        }

    def calculate_yoy_qoq(self, reports: List[dict]) -> dict:
        """计算同比和环比增长率"""
        if len(reports) < 2:
            return {}

        latest = reports[0]
        previous = reports[1]

        #简化计算：直接使用API返回的YoY
        return {
            "revenue_yoy": latest.get("revenue_yoy", 0),
            "revenue_qoq": self._calc_qoq(latest.get("total_revenue", 0), previous.get("total_revenue", 0)),
            "profit_yoy": latest.get("profit_yoy", 0),
            "profit_qoq": self._calc_qoq(latest.get("net_profit", 0), previous.get("net_profit", 0)),
        }

    def _calc_qoq(self, current: float, previous: float) -> float:
        """计算环比增长"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100

    def generate_financial_summary(self, date_str: str) -> List[dict]:
        """生成财务数据汇总"""
        all_data = self.load_financial_data(date_str)
        summaries = []

        for symbol, raw_data in all_data.items():
            parsed = self.parse_financial_report(raw_data, symbol)
            if parsed:
                # 添加收入分解
                segment_revenue = self.attribute_revenue_to_segments(
                    symbol, parsed.get("total_revenue", 0)
                )
                parsed["segment_revenue"] = segment_revenue
                summaries.append(parsed)

        # 按营收排序
        summaries.sort(key=lambda x: x.get("total_revenue", 0), reverse=True)
        return summaries


class RevenueTracker:
    """营收追踪器 -跟踪产业链各环节收入"""

    def __init__(self):
        self.layer_data = {
            "上游材料": {"revenue": 0, "companies": []},
            "上游设备": {"revenue": 0, "companies": []},
            "中游制造": {"revenue": 0, "companies": []},
            "中游封装": {"revenue": 0, "companies": []},
            "下游应用": {"revenue": 0, "companies": []},
        }

    def track_from_financials(self, financials: List[dict]):
        """从财务数据追踪各层收入"""
        for fin in financials:
            category = fin.get("category", "")
            segment_revenue = fin.get("segment_revenue", {})

            for segment, revenue in segment_revenue.items():
                if category in self.layer_data:
                    self.layer_data[category]["revenue"] += revenue
                    self.layer_data[category]["companies"].append({
                        "symbol": fin.get("symbol"),
                        "segment": segment,
                        "revenue": revenue,
                    })

    def get_layer_summary(self) -> dict:
        """获取层级汇总"""
        return self.layer_data


if __name__ == "__main__":
    analyzer = FinancialAnalyzer()
    summary = analyzer.generate_financial_summary("20250610")
    print(f"分析了 {len(summary)} 家公司的财务数据")
    for s in summary[:5]:
        print(f"{s['symbol']}: 营收 {s.get('total_revenue', 0):.2f}亿, YoY {s.get('revenue_yoy', 0):.1f}%")