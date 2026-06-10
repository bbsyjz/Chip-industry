"""
芯片产业链数据采集管道 - 新浪财经/腾讯版
使用可从海外访问的API
"""

import requests
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SINA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn/",
}

TENCENT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://gu.qq.com/",
}


def sina_request(url: str, timeout: int = 10) -> Optional[str]:
    """新浪财经API请求"""
    try:
        resp = requests.get(url, headers=SINA_HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.error(f"请求失败: {url} - {e}")
        return None


def get_sina_quote(symbol: str) -> Optional[dict]:
    """获取新浪财经股票行情"""
    # 转换代码:6开头加sh, 其他加sz
    if symbol.startswith("6"):
        sina_code = f"sh{symbol}"
    else:
        sina_code = f"sz{symbol}"

    url = f"https://hq.sinajs.cn/list={sina_code}"
    text = sina_request(url)
    if not text:
        return None

    # 解析: var hq_str_sh600519="贵州茅台,12.52,..."
    try:
        parts = text.strip().split('"')[1].split(",")
        if len(parts) < 10:
            return None

        name = parts[0]
        open_price = float(parts[1]) if parts[1] else 0
        close_prev = float(parts[2]) if parts[2] else 0  # 昨收
        current_price = float(parts[3]) if parts[3] else 0  # 当前/今收
        high = float(parts[4]) if parts[4] else 0
        low = parts[5]
        volume = float(parts[8]) if len(parts) > 8 and parts[8] else 0
        amount = float(parts[9]) if len(parts) > 9 and parts[9] else 0

        change_pct = 0
        if close_prev > 0:
            change_pct = ((current_price - close_prev) / close_prev) * 100

        return {
            "code": symbol,
            "name": name,
            "price": current_price,
            "open": open_price,
            "close_prev": close_prev,
            "high": high,
            "low": float(low) if low else 0,
            "volume": volume,
            "amount": amount,
            "change_pct": change_pct,
        }
    except Exception as e:
        logger.error(f"解析失败 {symbol}: {e}")
        return None


def get_sina_index(symbol: str) -> Optional[dict]:
    """获取新浪财经大盘指数"""
    # symbol: sh000001, sz399001
    url = f"https://hq.sinajs.cn/list=s_{symbol}"
    text = sina_request(url)
    if not text:
        return None

    try:
        parts = text.strip().split('"')[1].split(",")
        name = parts[0]
        price = float(parts[1]) if parts[1] else 0
        change = float(parts[2]) if len(parts) > 2 and parts[2] else 0
        change_pct = float(parts[3]) if len(parts) > 3 and parts[3] else 0
        volume = float(parts[4]) if len(parts) > 4 and parts[4] else 0
        amount = float(parts[5]) if len(parts) > 5 and parts[5] else 0

        return {
            "code": symbol,
            "name": name,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
            "amount": amount,
        }
    except Exception as e:
        logger.error(f"解析失败 {symbol}: {e}")
        return None


def get_sina_kline(symbol: str, period: str = "daily", count: int = 30) -> Optional[list]:
    """获取新浪财经K线数据"""
    # 转换代码
    if symbol.startswith("6"):
        sina_code = f"sh{symbol}"
    else:
        sina_code = f"sz{symbol}"

    # period: 240=日K, 300=周K, 400=月K
    period_map = {"daily": 240, "weekly": 300, "monthly": 400}
    scale = period_map.get(period, 240)

    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale={scale}&datalen={count}"

    try:
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        data = resp.json()
        return data
    except Exception as e:
        logger.error(f"K线获取失败 {symbol}: {e}")
        return None


def get_tencent_quote(symbol: str) -> Optional[dict]:
    """获取腾讯股票行情"""
    if symbol.startswith("6"):
        tencent_code = f"sh{symbol}"
    else:
        tencent_code = f"sz{symbol}"

    url = f"https://sqt.gtimg.cn/q={tencent_code}"
    try:
        resp = requests.get(url, headers=TENCENT_HEADERS, timeout=10)
        text = resp.text
        # 格式: v_sh600519="1~贵州茅台~600519~1275.88~1256.00~1252.08~..."
        content = text.strip().split('"')[1]
        parts = content.split("~")
        if len(parts) < 10:
            return None

        name = parts[1]
        current_price = float(parts[3]) if parts[3] else 0
        close_prev = float(parts[4]) if parts[4] else 0
        open_price = float(parts[5]) if parts[5] else 0
        volume = float(parts[6]) if parts[6] else 0

        change_pct = 0
        if close_prev > 0:
            change_pct = ((current_price - close_prev) / close_prev) * 100

        return {
            "code": symbol,
            "name": name,
            "price": current_price,
            "open": open_price,
            "close_prev": close_prev,
            "change_pct": change_pct,
            "volume": volume,
        }
    except Exception as e:
        logger.error(f"腾讯行情获取失败 {symbol}: {e}")
        return None


class SinaDataPipeline:
    """使用新浪财经的数据管道"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def collect_market_indices(self) -> List[dict]:
        """采集大盘指数"""
        logger.info("采集大盘指数...")
        indices = [
            "sh000001",  # 上证
            "sz399001",  # 深证
            "sh000300",  # 沪深300
            "sz399006",  # 创业板
        ]
        results = []
        for idx in indices:
            data = get_sina_index(idx)
            if data:
                results.append(data)
            time.sleep(0.1)
        return results

    def collect_all_quotes(self, delay: float = 0.15) -> List[dict]:
        """采集所有股票行情"""
        from stock_universe import get_all_stocks

        stocks = get_all_stocks()
        logger.info(f"采集 {len(stocks)} 只股票行情...")
        quotes = []
        for stock in stocks:
            #优先使用新浪，不行再用腾讯
            quote = get_sina_quote(stock["code"])
            if not quote:
                quote = get_tencent_quote(stock["code"])

            if quote:
                quote["category"] = stock["category"]
                quote["segment"] = stock["segment"]
                quotes.append(quote)
            time.sleep(delay)
        return quotes

    def collect_klines(self, period: str = "daily", count: int = 30) -> Dict[str, list]:
        """采集K线数据"""
        from stock_universe import get_all_stocks

        stocks = get_all_stocks()
        logger.info(f"采集 {len(stocks)} 只股票K线...")
        klines = {}
        for stock in stocks:
            kl = get_sina_kline(stock["code"], period, count)
            if kl:
                klines[stock["code"]] = kl
            time.sleep(0.2)
        return klines

    def save_daily_data(self, date_str: str, market_indices: list, quotes: list):
        """保存每日数据"""
        daily_dir = self.data_dir / "daily_quotes" / date_str
        daily_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "market_indices": market_indices,
            "quotes": quotes,
            "source": "sina_tencent",
        }

        with open(daily_dir / "quotes.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"数据已保存到 {daily_dir}")

    def run_daily_collection(self, date_str: str = None) -> dict:
        """执行每日数据采集"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        logger.info(f"开始每日数据采集: {date_str}")

        market_indices = self.collect_market_indices()
        quotes = self.collect_all_quotes()
        self.save_daily_data(date_str, market_indices, quotes)

        logger.info(f"每日数据采集完成: {len(quotes)} 只股票")
        return {
            "date": date_str,
            "market_indices": market_indices,
            "quotes": quotes,
        }


if __name__ == "__main__":
    pipeline = SinaDataPipeline()
    result = pipeline.run_daily_collection()
    print(f"采集完成: {len(result['quotes'])} 只股票")
    if result['quotes']:
        print(f"示例: {result['quotes'][0]}")