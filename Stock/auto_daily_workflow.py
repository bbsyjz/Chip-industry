#!/usr/bin/env python3
"""
每日自动工作流 - 采集数据、生成报告、推送到GitHub、发送微信通知
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from sina_data_pipeline import SinaDataPipeline
from html_report_generator import generate_html_report
from generate_docx import generate_docx_report
from webhook_notifier import WeChatNotifier, load_webhook_config


def run_workflow(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    print(f"========== 开始每日工作流: {date_str} ==========")

    # 1. 采集数据
    print("采集数据...")
    pipeline = SinaDataPipeline()
    data = pipeline.run_daily_collection(date_str)

    # 2. 生成报告
    print("生成报告...")
    output_dir = Path(__file__).parent / "data" / "supply_chain_reports" / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / "daily_digest.html"
    docx_path = output_dir / "daily_digest.docx"

    generate_html_report(date_str, data, str(html_path))
    generate_docx_report(date_str, data, str(docx_path))

    # 3. 推送到GitHub
    print("推送GitHub...")
    repo_dir = Path(__file__).parent.parent
    subprocess.run(["git", "add", f"Stock/data/supply_chain_reports/{date_str}/"], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Add daily report {date_str}"], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, env={**subprocess.os.environ, "GIT_HTTP2": "disable"}, capture_output=True)

    # 4. 发送微信通知
    print("发送微信通知...")
    config = load_webhook_config()
    notifier = WeChatNotifier(config['wechat_url'])

    html_url = f"https://bbsyjz.github.io/Chip-industry/Stock/data/supply_chain_reports/{date_str}/daily_digest.html"
    docx_url = f"https://raw.githubusercontent.com/bbsyjz/Chip-industry/main/Stock/data/supply_chain_reports/{date_str}/daily_digest.docx"

    quotes = data.get('quotes', [])
    indices = data.get('market_indices', [])

    message = f"""## 芯片产业链每日情报 {date_str}

### 大盘指数
"""

    for idx in indices:
        emoji = "📈" if idx.get('change_pct', 0) >= 0 else "📉"
        message += f"{emoji} *{idx.get('name')}*: {idx.get('price'):.2f} ({idx.get('change_pct'):+.2f}%)"

    message += f"""

###今日报告

📄 **HTML网页版**: {html_url}

📄 **Word文档下载**: {docx_url}

---
生成时间: {datetime.now().strftime('%H:%M:%S')}
由Claude Code自动生成"""

    notifier.send(message)

    print(f"========== 工作流完成: {date_str} ==========")
    return True


if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    run_workflow(date_str)