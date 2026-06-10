"""
芯片产业链每日情报PDF生成器
基于fpdf2，复用现有样式
"""

from fpdf import FPDF
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 颜色配置 (复用现有样式)
GREEN = (118, 185, 0)
LIGHT_BLUE = (0, 212, 255)
DARK_BLUE = (0, 119, 182)
ORANGE = (255, 107, 53)
PURPLE = (155, 89, 182)
RED = (231, 76, 60)
DARK_BG = (13, 27, 42)
LIGHT_GRAY = (224, 224, 224)
MID_GRAY = (136, 136, 136)
WHITE = (255, 255, 255)

FONT_PATH = "/tmp/fonts/HiraginoSansGB-Regular.ttf"


class DailyDigestPDF(FPDF):
    """每日情报PDF生成器"""

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('hsgb', '', 8)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 10, f'- Page {self.page_no()} -', align='C')

    def section_header(self, title: str, color: tuple):
        """章节标题"""
        self.set_fill_color(*color)
        self.set_text_color(*WHITE)
        self.set_font('hsgb', '', 13)
        self.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT', fill=True)
        self.set_text_color(*LIGHT_GRAY)
        self.ln(4)

    def stock_table(self, headers: List[str], rows: List[List], col_widths: List[float],
                    header_color: tuple = DARK_BG):
        """股票数据表格"""
        self.set_fill_color(*header_color)
        self.set_text_color(*GREEN)
        self.set_font('hsgb', '', 7)
        total = sum(col_widths)
        scale = (210 - 36) / total if total > 0 else 1
        widths = [w * scale for w in col_widths]
        for i, h in enumerate(headers):
            self.cell(widths[i], 5.5, h, border=1, fill=True)
        self.ln()
        self.set_font('hsgb', '', 6.5)
        self.set_text_color(*LIGHT_GRAY)
        fill = False
        for row in rows:
            self.set_fill_color(*DARK_BG if not fill else (15, 21, 32))
            for i, cell in enumerate(row):
                self.cell(widths[i], 5, str(cell)[:80], border=1, fill=True)
            self.ln()
            fill = not fill
        self.ln(2)

    def add_cover_page(self, date_str: str, market_indices: List[dict], top_gainers: List[dict],
                       top_losers: List[dict]):
        """封面页"""
        self.add_page()
        self.set_fill_color(*DARK_BG)
        self.rect(0, 0, 210, 297, 'F')

        # 标题
        self.set_font('hsgb', '', 10)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 8, 'CHIP INDUSTRY SUPPLY CHAIN', new_x='LMARGIN', new_y='NEXT', align='C')
        self.ln(10)

        self.set_font('hsgb', '', 24)
        self.set_text_color(*LIGHT_BLUE)
        self.cell(0, 15, 'DAILY DIGEST', new_x='LMARGIN', new_y='NEXT', align='C')

        self.set_font('hsgb', '', 16)
        self.set_text_color(*PURPLE)
        self.cell(0, 10, date_str, new_x='LMARGIN', new_y='NEXT', align='C')
        self.ln(15)

        # 大盘指数
        self.section_header("MARKET OVERVIEW", DARK_BLUE)
        index_headers = ["Index", "Close", "Change %"]
        index_widths = [60, 50, 40]
        index_rows = []
        for idx in market_indices:
            change_str = f"{idx.get('change_pct', 0):+.2f}%"
            index_rows.append([
                idx.get('name', ''),
                f"{idx.get('price', 0):.2f}",
                change_str
            ])
        self.stock_table(index_headers, index_rows, index_widths)

        # 涨跌排行
        self.section_header("TOP MOVERS", GREEN if top_gainers else RED)
        if top_gainers:
            gain_headers = ["Top Gainers", "Price", "Change %"]
            gain_widths = [70, 40, 40]
            gain_rows = [[s.get('name', ''), f"{s.get('price', 0):.2f}", f"{s.get('change_pct', 0):+.2f}%"]
                         for s in top_gainers[:5]]
            self.stock_table(gain_headers, gain_rows, gain_widths)

        if top_losers:
            loss_headers = ["Top Losers", "Price", "Change %"]
            loss_widths = [70, 40, 40]
            loss_rows = [[s.get('name', ''), f"{s.get('price', 0):.2f}", f"{s.get('change_pct', 0):+.2f}%"]
                         for s in top_losers[:5]]
            self.stock_table(loss_headers, loss_rows, loss_widths)

    def add_quotes_page(self, quotes: List[dict], category: str):
        """行情详情页"""
        self.add_page()
        self.section_header(f"{category.upper()} - STOCK QUOTES", DARK_BLUE)

        headers = ["Code", "Name", "Price", "Change %", "PE", "PB", "Mkt Cap(B)"]
        widths = [30, 45, 30, 30, 25, 25, 35]

        category_quotes = [q for q in quotes if q.get('category') == category]
        if not category_quotes:
            self.set_text_color(*MID_GRAY)
            self.set_font('hsgb', '', 9)
            self.cell(0, 10, "No data available", new_x='LMARGIN', new_y='NEXT', align='C')
            return

        rows = []
        for q in category_quotes:
            rows.append([
                q.get('code', ''),
                q.get('name', '')[:10],
                f"{q.get('price', 0):.2f}",
                f"{q.get('change_pct', 0):+.2f}%",
                f"{q.get('pe', 0):.1f}" if q.get('pe', 0) > 0 else "-",
                f"{q.get('pb', 0):.2f}" if q.get('pb', 0) > 0 else "-",
                f"{q.get('market_cap', 0):.1f}"
            ])
        self.stock_table(headers, rows, widths)

    def add_financial_page(self, financials: List[dict]):
        """财务数据页"""
        self.add_page()
        self.section_header("FINANCIAL HIGHLIGHTS", PURPLE)

        if not financials:
            self.set_text_color(*MID_GRAY)
            self.set_font('hsgb', '', 9)
            self.cell(0, 10, "No financial data available", new_x='LMARGIN', new_y='NEXT', align='C')
            return

        headers = ["Code", "Revenue(M)", "Rev YoY%", "Net Profit(M)", "NP YoY%", "Margin%"]
        widths = [30, 40, 30, 40, 30, 30]

        rows = []
        for f in financials[:20]:
            revenue = f.get('total_revenue', 0) * 100  # 亿元 -> 百万元
            profit = f.get('net_profit', 0) * 100
            margin = f.get('net_margin', 0)
            rows.append([
                f.get('symbol', ''),
                f"{revenue:.0f}",
                f"{f.get('revenue_yoy', 0):+.1f}%",
                f"{profit:.0f}",
                f"{f.get('profit_yoy', 0):+.1f}%",
                f"{margin:.1f}%" if margin else "-"
            ])
        self.stock_table(headers, rows, widths)

    def add_news_page(self, news: Dict[str, List[dict]]):
        """新闻公告页"""
        self.add_page()
        self.section_header("NEWS & ANNOUNCEMENTS", ORANGE)

        for symbol, news_list in list(news.items())[:10]:
            if not news_list:
                continue
            self.set_font('hsgb', '', 8)
            self.set_text_color(*LIGHT_BLUE)
            self.cell(0, 6, f"[{symbol}]", new_x='LMARGIN', new_y='NEXT')
            for n in news_list[:3]:
                self.set_font('hsgb', '', 7)
                self.set_text_color(*LIGHT_GRAY)
                title = n.get('title', '')[:80]
                time_str = n.get('publish_time', '')[:10]
                self.cell(0, 5, f"  {time_str} - {title}", new_x='LMARGIN', new_y='NEXT')
            self.ln(3)

    def add_sentiment_indicator(self, quotes: List[dict]):
        """产业链情绪指数"""
        self.add_page()
        self.section_header("SUPPLY CHAIN SENTIMENT", GREEN)

        categories = ["上游材料", "上游设备", "中游制造", "中游封装", "下游应用"]
        self.set_font('hsgb', '', 9)

        for cat in categories:
            cat_quotes = [q for q in quotes if q.get('category') == cat]
            if not cat_quotes:
                continue

            # 计算平均涨跌
            changes = [q.get('change_pct', 0) for q in cat_quotes]
            avg_change = sum(changes) / len(changes) if changes else 0

            # 生成情绪条
            bar_len = int(abs(avg_change) / 2) if abs(avg_change) > 0 else 0
            bar_len = min(bar_len, 50)
            bar = "█" * bar_len + "░" * (50 - bar_len)

            color = GREEN if avg_change >= 0 else RED
            self.set_text_color(*color)
            self.cell(40, 6, f"{cat}:", new_x='LMARGIN', new_y='NEXT')
            self.set_text_color(*LIGHT_GRAY)
            self.cell(0, 6, f"{bar} {avg_change:+.2f}%", new_x='LMARGIN', new_y='NEXT')
            self.ln(2)


def generate_daily_digest(date_str: str, data: dict, output_path: str):
    """生成每日情报PDF"""
    pdf = DailyDigestPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=18)
    try:
        pdf.add_font('hsgb', '', FONT_PATH)
    except:
        logger.warning(f"字体文件未找到: {FONT_PATH}, 使用默认字体")

    market_indices = data.get('market_indices', [])
    quotes = data.get('quotes', [])
    financials = data.get('financials', [])
    news = data.get('news', {})

    #排序涨跌
    sorted_quotes = sorted(quotes, key=lambda x: x.get('change_pct', 0), reverse=True)
    top_gainers = sorted_quotes[:5]
    top_losers = sorted_quotes[-5:] if len(sorted_quotes) >= 5 else sorted_quotes

    # 封面页
    pdf.add_cover_page(date_str, market_indices, top_gainers, top_losers)

    # 各层级行情
    categories = ["上游材料", "上游设备", "中游制造", "中游封装", "下游应用"]
    for cat in categories:
        cat_quotes = [q for q in quotes if q.get('category') == cat]
        if cat_quotes:
            pdf.add_quotes_page(quotes, cat)

    # 情绪指数
    pdf.add_sentiment_indicator(quotes)

    # 财务数据
    if financials:
        pdf.add_financial_page(financials)

    # 新闻
    if news:
        pdf.add_news_page(news)

    # 保存
    pdf.output(output_path)
    logger.info(f"PDF已生成: {output_path}")


if __name__ == "__main__":
    # 测试
    test_data = {
        "date": "20250610",
        "market_indices": [
            {"name": "上证指数", "price": 3300.25, "change_pct": 1.25},
            {"name": "深证成指", "price": 10500.50, "change_pct": 0.85},
            {"name": "沪深300", "price": 3900.00, "change_pct": 1.10},
        ],
        "quotes": [
            {"code": "688981", "name": "中芯国际", "price": 52.30, "change_pct": 2.15,
             "pe": 35.2, "pb": 3.8, "market_cap": 4200, "category": "中游制造"},
            {"code": "002916", "name": "深南电路", "price": 98.50, "change_pct": 5.25,
             "pe": 28.5, "pb": 4.2, "market_cap": 850, "category": "中游封装"},
        ],
        "financials": [],
        "news": {},
    }
    from pathlib import Path
    output = Path(__file__).parent / "data" / "test_digest.pdf"
    output.parent.mkdir(exist_ok=True)
    generate_daily_digest("20250610", test_data, str(output))
    print(f"测试PDF已生成: {output}")