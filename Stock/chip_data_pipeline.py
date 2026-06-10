"""
芯片产业链数据采集管道
批量采集行情、K线、新闻、财报数据
"""

import requests
import time
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
from pathlib import Path

from stock_universe import get_all_stocks, MARKET_INDICES, INDEX_CODES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.eastmoney.com/",
}

BASE_URL = "https://push2.eastmoney.com"
SEARCH_URL = "https://searchapi.eastmoney.com"
REPORT_URL = "https://emreport.eastmoney.com"
NOTICE_URL = "https://np-anotice-stock.eastmoney.com"


def em_request(url: str, params: dict = None, timeout: int = 15) -> Optional[dict]:
    """东方财富API请求"""
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"请求失败: {url} - {e}")
        return None


def get_stock_quote(symbol: str) -> Optional[dict]:
    """获取股票实时行情"""
    # 转换代码格式
    if symbol.startswith("6"):
        secid = f"1.{symbol}"
    else:
        secid = f"0.{symbol}"

    url = f"{BASE_URL}/api/qt/stock/get"
    params = {
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
        "secid": secid,
    }

    data = em_request(url, params)
    if not data or "data" not in data:
        return None

    d = data["data"]
    return {
        "code": symbol,
        "name": d.get("f14", ""),
        "price": d.get("f2", 0),
        "change_pct": d.get("f3", 0),
        "change_amount": d.get("f4", 0),
        "volume": d.get("f5", 0),
        "amount": d.get("f6", 0),
        "amplitude": d.get("f7", 0),
        "turnover_rate": d.get("f8", 0),
        "pe": d.get("f9", 0),
        "pb": d.get("f10", 0),
        "market_cap": d.get("f20", 0) / 100000000 if d.get("f20") else 0,  # 亿元
        "float_market_cap": d.get("f21", 0) / 100000000 if d.get("f21") else 0,
    }


def get_stock_kline(symbol: str, period: str = "daily", count: int = 30) -> Optional[list]:
    """获取股票K线数据"""
    if symbol.startswith("6"):
        secid = f"1.{symbol}"
    else:
        secid = f"0.{symbol}"

    url = f"{BASE_URL}/api/qt/stock/kline/get"
    period_map = {"daily": 101, "weekly": 102, "monthly": 103, "min60": 60, "min30": 30, "min15": 15, "min5": 5}
    params = {
        "klt": period_map.get(period, 101),
        "fqt": 1,  # 前复权
        "lmt": count,
        "secid": secid,
    }

    data = em_request(url, params)
    if not data or "data" not in data:
        return None

    klines = data["data"].get("klines", [])
    result = []
    for kl in klines:
        parts = kl.split(",")
        if len(parts) >= 6:
            result.append({
                "date": parts[0],
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": float(parts[5]),
            })
    return result


def get_market_quotation(indices: List[str]) -> List[dict]:
    """获取大盘指数行情"""
    results = []
    for idx in indices:
        if idx.startswith("sh"):
            secid = f"1.{idx[2:]}"
        elif idx.startswith("sz"):
            secid = f"0.{idx[2:]}"
        else:
            continue

        url = f"{BASE_URL}/api/qt/stock/get"
        params = {
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f12,f14",
            "secid": secid,
        }

        data = em_request(url, params)
        if not data or "data" not in data:
            continue

        d = data["data"]
        #找到对应的指数名称
        name = next((i["name"] for i in MARKET_INDICES if i["code"] == idx), idx)
        results.append({
            "code": idx,
            "name": name,
            "price": d.get("f2", 0),
            "change_pct": d.get("f3", 0),
            "change_amount": d.get("f4", 0),
            "volume": d.get("f5", 0),
            "amount": d.get("f6", 0),
        })
        time.sleep(0.1)
    return results


def get_financial_report(symbol: str, report_type: str = "annual") -> Optional[dict]:
    """获取股票财务报告"""
    url = f"{REPORT_URL}/pc/cssgs/getFinancialSummaryData"
    params = {
        "stockCode": symbol,
        "reportType": report_type,
        "count": 4,
    }
    return em_request(url, params)


def get_stock_news(symbol: str, count: int = 10) -> List[dict]:
    """获取股票新闻和公告"""
    url = f"{NOTICE_URL}/api/security/ann"
    params = {
        "sr": -1,
        "page_size": count,
        "page_index": 1,
        "ann_type": "ALL",
        "stock_list": symbol,
    }

    data = em_request(url, params)
    if not data or "data" not in data:
        return []

    notices = data["data"].get("list", [])
    return [
        {
            "title": n.get("title", ""),
            "publish_time": n.get("publish_time", ""),
            "type": n.get("notice_type", ""),
            "url": n.get("art_url", ""),
        }
        for n in notices[:count]
    ]


class ChipDataPipeline:
    """芯片产业链数据采集管道"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def collect_market_indices(self) -> List[dict]:
        """采集大盘指数"""
        logger.info("采集大盘指数...")
        return get_market_quotation(INDEX_CODES)

    def collect_all_quotes(self, delay: float = 0.1) -> List[dict]:
        """采集所有股票行情"""
        stocks = get_all_stocks()
        logger.info(f"采集 {len(stocks)} 只股票行情...")
        quotes = []
        for stock in stocks:
            quote = get_stock_quote(stock["code"])
            if quote:
                quote["category"] = stock["category"]
                quote["segment"] = stock["segment"]
                quotes.append(quote)
            time.sleep(delay)
        return quotes

    def collect_klines(self, period: str = "daily", count: int = 30, delay: float = 0.1) -> Dict[str, list]:
        """采集所有股票K线数据"""
        stocks = get_all_stocks()
        logger.info(f"采集 {len(stocks)} 只股票K线数据...")
        klines = {}
        for stock in stocks:
            kl = get_stock_kline(stock["code"], period, count)
            if kl:
                klines[stock["code"]] = kl
            time.sleep(delay)
        return klines

    def collect_financial_reports(self, delay: float = 0.2) -> Dict[str, dict]:
        """采集所有股票财务报告"""
        stocks = get_all_stocks()
        logger.info(f"采集 {len(stocks)} 只股票财务报告...")
        reports = {}
        for stock in stocks:
            report = get_financial_report(stock["code"])
            if report:
                reports[stock["code"]] = report
            time.sleep(delay)
        return reports

    def collect_news(self, count: int = 5, delay: float = 0.1) -> Dict[str, list]:
        """采集所有股票新闻"""
        stocks = get_all_stocks()
        logger.info(f"采集 {len(stocks)} 只股票新闻...")
        all_news = {}
        for stock in stocks:
            news = get_stock_news(stock["code"], count)
            if news:
                all_news[stock["code"]] = news
            time.sleep(delay)
        return all_news

    def save_daily_data(self, date_str: str, market_indices: list, quotes: list,
                        klines: Dict = None, financials: Dict = None, news: Dict = None):
        """保存每日数据"""
        daily_dir = self.data_dir / "daily_quotes" / date_str
        daily_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "market_indices": market_indices,
            "quotes": quotes,
        }

        # 保存主数据
        with open(daily_dir / "quotes.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存K线数据
        if klines:
            kline_dir = self.data_dir / "klines" / date_str
            kline_dir.mkdir(parents=True, exist_ok=True)
            for code, kl in klines.items():
                with open(kline_dir / f"{code}.json", "w", encoding="utf-8") as f:
                    json.dump(kl, f, ensure_ascii=False, indent=2)

        # 保存财报数据
        if financials:
            fin_dir = self.data_dir / "financials" / date_str
            fin_dir.mkdir(parents=True, exist_ok=True)
            for code, report in financials.items():
                with open(fin_dir / f"{code}.json", "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)

        # 保存新闻数据
        if news:
            news_dir = self.data_dir / "news" / date_str
            news_dir.mkdir(parents=True, exist_ok=True)
            for code, news_list in news.items():
                with open(news_dir / f"{code}.json", "w", encoding="utf-8") as f:
                    json.dump(news_list, f, ensure_ascii=False, indent=2)

        logger.info(f"数据已保存到 {daily_dir}")

    def run_daily_collection(self, date_str: str = None):
        """执行每日数据采集"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        logger.info(f"开始每日数据采集: {date_str}")

        # 1. 采集大盘指数
        market_indices = self.collect_market_indices()

        # 2. 采集所有股票行情
        quotes = self.collect_all_quotes()

        # 3. 保存数据
        self.save_daily_data(date_str, market_indices, quotes)

        logger.info(f"每日数据采集完成: {date_str}")
        return {
            "date": date_str,
            "market_indices": market_indices,
            "quotes": quotes,
        }


if __name__ == "__main__":
    pipeline = ChipDataPipeline()
    result = pipeline.run_daily_collection()
    print(f"采集完成: {len(result['quotes'])} 只股票")