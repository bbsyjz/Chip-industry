from webhook_notifier import WeChatNotifier, load_webhook_config
from datetime import datetime

date_str = "20260610"
html_url = "https://bbsyjz.github.io/Chip-industry/Stock/data/supply_chain_reports/20260610/daily_digest.html"
docx_url = "https://raw.githubusercontent.com/bbsyjz/Chip-industry/main/Stock/data/supply_chain_reports/20260610/daily_digest.docx"

message = f"""## 芯片产业链每日情报 {date_str}

###今日报告（已更新）

📄 **HTML网页版**: {html_url}

📄 **Word文档下载**: {docx_url}

**成交量TOP15表格已修正：**
- 成交量单位：万股
- 成交额单位：亿元
- 保留两位小数

---
生成时间: {datetime.now().strftime('%H:%M:%S')}
由Claude Code自动生成"""

config = load_webhook_config()
notifier = WeChatNotifier(config['wechat_url'])
result = notifier.send(message)
print('发送结果:', '成功' if result else '失败')