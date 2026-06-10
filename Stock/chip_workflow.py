#!/usr/bin/env python3
"""
芯片产业链每日情报工作流 - 主调度器
整合数据采集、财报分析、报告生成、通知推送
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from sina_data_pipeline import SinaDataPipeline
from financial_analyzer import FinancialAnalyzer
from daily_digest_generator import generate_daily_digest
from webhook_notifier import (
    create_notifier_from_config,
    format_daily_digest_message
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chip_workflow.log'),
    ]
)
logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = Path(__file__).parent / "data"
REPORT_DIR = DATA_DIR / "supply_chain_reports"


class ChipWorkflow:
    """芯片产业链工作流调度器"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(exist_ok=True)
        self.pipeline = SinaDataPipeline(str(self.data_dir))
        self.analyzer = FinancialAnalyzer(str(self.data_dir))
        self.notifier = create_notifier_from_config()

    def run_daily_collection(self, date_str: str = None) -> dict:
        """执行每日数据采集"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        logger.info(f"========== 开始每日数据采集: {date_str} ==========")

        # 1. 采集大盘指数和股票行情
        market_indices = self.pipeline.collect_market_indices()
        quotes = self.pipeline.collect_all_quotes()

        # 保存采集的数据
        self.pipeline.save_daily_data(date_str, market_indices, quotes)

        logger.info(f"数据采集完成: {len(quotes)} 只股票")

        return {
            "date": date_str,
            "market_indices": market_indices,
            "quotes": quotes,
        }

    def collect_financials(self, date_str: str = None) -> dict:
        """采集财务数据"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        logger.info(f"========== 采集财务数据: {date_str} ==========")
        financials = self.pipeline.collect_financial_reports()

        # 保存财务数据
        fin_dir = self.data_dir / "financials" / date_str
        fin_dir.mkdir(parents=True, exist_ok=True)
        for symbol, report in financials.items():
            with open(fin_dir / f"{symbol}.json", "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"财务数据采集完成: {len(financials)}家公司")
        return financials

    def collect_news(self, date_str: str = None) -> dict:
        """采集新闻"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        logger.info(f"========== 采集新闻: {date_str} ==========")
        news = self.pipeline.collect_news()

        # 保存新闻数据
        news_dir = self.data_dir / "news" / date_str
        news_dir.mkdir(parents=True, exist_ok=True)
        for symbol, news_list in news.items():
            with open(news_dir / f"{symbol}.json", "w", encoding="utf-8") as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2)

        logger.info(f"新闻采集完成: {len(news)} 只股票")
        return news

    def generate_report(self, date_str: str, data: dict, financials: dict = None,
                        news: dict = None) -> str:
        """生成每日PDF报告"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        logger.info(f"========== 生成报告: {date_str} ==========")

        # 解析财务数据
        financial_summaries = []
        if financials:
            for symbol, raw_data in financials.items():
                parsed = self.analyzer.parse_financial_report(raw_data, symbol)
                if parsed:
                    financial_summaries.append(parsed)

        #报告输出目录
        report_date_dir = REPORT_DIR / date_str
        report_date_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = report_date_dir / "daily_digest.pdf"

        # 添加财务数据到data
        report_data = {
            **data,
            "financials": financial_summaries,
            "news": news or {}
        }

        # 生成PDF
        generate_daily_digest(date_str, report_data, str(pdf_path))

        logger.info(f"PDF报告已生成: {pdf_path}")
        return str(pdf_path)

    def send_notification(self, date_str: str, data: dict, pdf_path: str = None):
        """发送通知"""
        logger.info("========== 发送通知 ==========")

        # 格式化消息
        message = format_daily_digest_message(date_str, data)
        if pdf_path:
            message += f"\n\n📄完整报告: `{pdf_path}`"

        # 发送通知
        if self.notifier.notifiers:
            result = self.notifier.send_all(message)
            logger.info(f"通知发送结果: {result}")
        else:
            logger.info("未配置webhook，跳过通知")

    def run_full_workflow(self, date_str: str = None, skip_collection: bool = False) -> str:
        """执行完整工作流"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        logger.info(f"========== 启动完整工作流: {date_str} ==========")

        # 1. 数据采集
        if not skip_collection:
            data = self.run_daily_collection(date_str)
        else:
            # 从已有数据加载
            quotes_file = self.data_dir / "daily_quotes" / date_str / "quotes.json"
            if quotes_file.exists():
                with open(quotes_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                logger.error(f"数据文件不存在: {quotes_file}")
                raise FileNotFoundError(f"请先运行数据采集: {quotes_file}")

        # 2. 财务数据
        financials = self.collect_financials(date_str)

        # 3. 新闻
        news = self.collect_news(date_str)

        # 4. 生成报告
        pdf_path = self.generate_report(date_str, data, financials, news)

        # 5. 发送通知
        self.send_notification(date_str, data, pdf_path)

        logger.info(f"========== 工作流完成: {date_str} ==========")
        return pdf_path


def run_as_scheduler():
    """定时执行模式"""
    import time
    logger.info("启动定时工作流模式，每5分钟检查一次")

    workflow = ChipWorkflow()

    while True:
        now = datetime.now()
        current_time = now.time()

        # 检查是否应该执行 (收盘后 22:00-23:00)
        if current_time.hour == 22 and current_time.minute >= 0:
            try:
                date_str = now.strftime("%Y%m%d")
                workflow.run_full_workflow(date_str)
            except Exception as e:
                logger.error(f"工作流执行失败: {e}")

            # 执行后休眠1小时避免重复执行
            time.sleep(3600)
        else:
            time.sleep(300)  # 每5分钟检查


def main():
    parser = argparse.ArgumentParser(description="芯片产业链每日情报工作流")
    parser.add_argument("--date", "-d", help="日期 (YYYYMMDD格式)")
    parser.add_argument("--skip-collection", "-s", action="store_true", help="跳过数据采集")
    parser.add_argument("--scheduler", action="store_true", help="定时执行模式")
    parser.add_argument("--collect-only", action="store_true", help="仅采集数据")

    args = parser.parse_args()

    if args.scheduler:
        run_as_scheduler()
        return

    workflow = ChipWorkflow()

    if args.collect_only:
        # 仅采集数据
        data = workflow.run_daily_collection(args.date)
        print(f"采集完成: {len(data['quotes'])} 只股票")
    else:
        # 完整工作流
        pdf_path = workflow.run_full_workflow(args.date, args.skip_collection)
        print(f"工作流完成，报告: {pdf_path}")


if __name__ == "__main__":
    main()