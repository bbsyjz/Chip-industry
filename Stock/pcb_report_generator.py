#!/usr/bin/env python3
"""
东方财富PCB板块分析 - PDF报告生成
"""

import json
import time
import logging
from datetime import datetime
from typing import Optional

import requests
from fpdf import FPDF

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.eastmoney.com"
}

# 东方财富K线API正确路径
KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"


def em_request(url: str, params: dict = None, timeout: int = 15) -> Optional[dict]:
    """东方财富API请求"""
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"请求失败: {e}")
        return None


def get_stock_price_change(code: str, start_date: str = "20260101") -> Optional[dict]:
    """获取股票区间涨跌幅"""
    secid = f"1.{code}" if code.startswith("6") else f"0.{code}"

    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": 101,  # 日K
        "fqt": 1,    # 前复权
        "secid": secid,
        "beg": start_date,
        "end": "20500101",
        "lmt": 250,  # 限制数量
        "ut": "fa5fd1943c7b386f172d6893dbbd5d1d"
    }

    result = em_request(KLINE_URL, params)
    if result and result.get("data"):
        klines = result["data"].get("klines", [])
        if len(klines) >= 2:
            first_close = float(klines[0].split(",")[2])
            last_close = float(klines[-1].split(",")[2])
            change_pct = ((last_close - first_close) / first_close) * 100
            return {
                "start_price": first_close,
                "end_price": last_close,
                "change_pct": change_pct,
                "current_price": last_close
            }
    return None


def get_market_cap(code: str) -> Optional[float]:
    """获取市值（亿元）"""
    secid = f"1.{code}" if code.startswith("6") else f"0.{code}"

    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "secid": secid,
        "fields": "f20,f21,f116,f117",
        "ut": "fa5fd1943c7b386f172d6893dbbd5d1d"
    }

    result = em_request(url, params)
    if result and result.get("data"):
        data = result["data"]
        # 市值单位可能是万，需要转换
        mkt = data.get("f20", 0)
        if mkt:
            return round(mkt / 100000000, 2)  # 转换为亿元
    return 0


def get_financial_summary(code: str) -> dict:
    """获取财务数据摘要"""
    secid = f"1.{code}" if code.startswith("6") else f"0.{code}"

    # 东方财富财务数据接口
    url = "https://emreport.eastmoney.com/pc/cssgs/getFinancialSummaryData"
    params = {"code": code}

    result = em_request(url, params)
    if result:
        return result

    return {}


class PCBReportPDF(FPDF):
    """PCB板块分析PDF"""

    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'PCB BAN KUAI FEN XI BAO GAO', new_x="LMARGIN", new_y="NEXT", align='C')
        self.set_font('Helvetica', '', 9)
        self.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def create_pdf_report(stocks: list, output_path: str):
    """生成PDF报告"""
    pdf = PCBReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ============ Page 1: Cover ============
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 20)
    pdf.ln(25)
    pdf.cell(0, 12, 'PCB BAN KUAI ZHUAN QI FEN XI', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, f'Period: 2026-01-01 to {datetime.now().strftime("%Y-%m-%d")}', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, f'Total Stocks: {len(stocks)}', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, f'Report Date: {datetime.now().strftime("%Y-%m-%d")}', new_x="LMARGIN", new_y="NEXT", align='C')

    # ============ Page 2: Top 20 ============
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'TOP 20 STOCKS BY GAIN', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Table header
    pdf.set_fill_color(50, 50, 100)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(15, 7, 'Rank', border=1, align='C', fill=True)
    pdf.cell(25, 7, 'Code', border=1, align='C', fill=True)
    pdf.cell(45, 7, 'Name', border=1, align='C', fill=True)
    pdf.cell(30, 7, 'Gain %', border=1, align='C', fill=True)
    pdf.cell(30, 7, 'Price', border=1, align='C', fill=True)
    pdf.cell(30, 7, 'Mkt Cap(B)', border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    for i, s in enumerate(stocks[:20]):
        fill = (i % 2 == 0)
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(15, 7, str(i+1), border=1, align='C', fill=fill)
        pdf.cell(25, 7, s.get("code", ""), border=1, align='C', fill=fill)
        pdf.cell(45, 7, s.get("name", ""), border=1, align='C', fill=fill)
        pdf.cell(30, 7, f"{s.get('gain', 0):.2f}%", border=1, align='C', fill=fill)
        pdf.cell(30, 7, f"{s.get('price', 0):.2f}", border=1, align='C', fill=fill)
        pdf.cell(30, 7, f"{s.get('mkt_cap', 0):.2f}", border=1, align='C', fill=fill)
        pdf.ln()

    # ============ Page 3: Full List ============
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'FULL LIST (TOP 50)', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Table header
    pdf.set_fill_color(50, 50, 100)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', '', 7)
    pdf.cell(12, 6, 'Rank', border=1, align='C', fill=True)
    pdf.cell(22, 6, 'Code', border=1, align='C', fill=True)
    pdf.cell(40, 6, 'Name', border=1, align='C', fill=True)
    pdf.cell(25, 6, 'Gain %', border=1, align='C', fill=True)
    pdf.cell(25, 6, 'Start Prc', border=1, align='C', fill=True)
    pdf.cell(25, 6, 'End Prc', border=1, align='C', fill=True)
    pdf.cell(25, 6, 'Mkt Cap(B)', border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    for i, s in enumerate(stocks[:50]):
        fill = (i % 2 == 0)
        pdf.set_font('Helvetica', '', 7)
        pdf.cell(12, 6, str(i+1), border=1, align='C', fill=fill)
        pdf.cell(22, 6, s.get("code", ""), border=1, align='C', fill=fill)
        pdf.cell(40, 6, s.get("name", ""), border=1, align='C', fill=fill)
        pdf.cell(25, 6, f"{s.get('gain', 0):.2f}%", border=1, align='C', fill=fill)
        pdf.cell(25, 6, f"{s.get('start_price', 0):.2f}", border=1, align='C', fill=fill)
        pdf.cell(25, 6, f"{s.get('end_price', 0):.2f}", border=1, align='C', fill=fill)
        pdf.cell(25, 6, f"{s.get('mkt_cap', 0):.2f}", border=1, align='C', fill=fill)
        pdf.ln()

    pdf.output(output_path)
    logger.info(f"PDF saved: {output_path}")


# 主要PCB股票列表（基于行业地位筛选）
PCB_STOCKS = [
    {"code": "002916", "name": "DeepBlue Circuit"},
    {"code": "600183", "name": "Shengyi Tech"},
    {"code": "002463", "name": "Wus Circuit"},
    {"code": "002384", "name": "Dongshan Precision"},
    {"code": "002938", "name": "Pengding Holding"},
    {"code": "000823", "name": "Ultrasonic Electronic"},
    {"code": "300476", "name": "Victory Giant Tech"},
    {"code": "002861", "name": "King Bright"},
    {"code": "002636", "name": "Anjie Tech"},
    {"code": "603186", "name": "Huazheng New Material"},
    {"code": "603228", "name": "Jingwang Electronic"},
    {"code": "300739", "name": "KaiPu Bio"},
    {"code": "002134", "name": "Tianjin Puleng"},
    {"code": "002541", "name": "Honglu Steel"},
    {"code": "600601", "name": "Zhiguang Electronic"},
    {"code": "002180", "name": "Nasa"},
    {"code": "300604", "name": "Changdian Tech"},
    {"code": "002309", "name": "Lianchuang Electronic"},
    {"code": "300408", "name": "Sunnyside Tech"},
    {"code": "002655", "name": "Jiangsu Huaneng"},
    {"code": "603659", "name": "Putailai"},
    {"code": "300682", "name": "Nanjing Loyal"},
    {"code": "300460", "name": "Fenghua Circuit"},
    {"code": "002045", "name": "Guangzhou Yisheng"},
    {"code": "000581", "name": "Weifu HighTech"},
    {"code": "002156", "name": "Tongfang Singamus"},
    {"code": "603160", "name": "UNISOC"},
    {"code": "688126", "name": "Shanghai Xinzhi"},
    {"code": "688799", "name": "Hualong Rest"},
    {"code": "688521", "name": "CSoC"},
]


def main():
    logger.info("Starting PCB analysis...")

    results = []
    for i, stock in enumerate(PCB_STOCKS):
        code = stock["code"]
        name = stock["name"]
        logger.info(f"[{i+1}/{len(PCB_STOCKS)}] Processing {code} {name}")

        # 获取价格数据
        price_data = get_stock_price_change(code, "20260101")
        if price_data:
            stock["gain"] = price_data["change_pct"]
            stock["start_price"] = price_data["start_price"]
            stock["end_price"] = price_data["end_price"]
            stock["price"] = price_data["current_price"]
        else:
            stock["gain"] = 0
            stock["start_price"] = 0
            stock["end_price"] = 0
            stock["price"] = 0

        # 获取市值
        mkt_cap = get_market_cap(code)
        stock["mkt_cap"] = mkt_cap

        results.append(stock)
        time.sleep(0.1)

    # 按涨幅排序
    results.sort(key=lambda x: x.get("gain", 0), reverse=True)

    # 限制前50
    results = results[:50]

    # 保存JSON
    json_path = "/Users/bbsyjz/my-first-project/Stock/pcb_analysis_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 生成PDF
    pdf_path = "/Users/bbsyjz/my-first-project/Stock/PCB_BanKuai_FenXi.pdf"
    create_pdf_report(results, pdf_path)

    logger.info(f"Done! Results: {json_path}")
    return results


if __name__ == "__main__":
    main()