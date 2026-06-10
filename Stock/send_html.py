import json
from pathlib import Path
from webhook_notifier import WeChatNotifier, load_webhook_config
from datetime import datetime

# 加载数据
with open('data/daily_quotes/20260610/quotes.json', 'r') as f:
    data = json.load(f)

quotes = data.get('quotes', [])
indices = data.get('market_indices', [])

# 按产业链分组统计
from html_report_generator import get_stock_detail

categories = {"上游材料": [], "上游设备": [], "中游制造": [], "中游封装": [], "下游应用": []}
for q in quotes:
    cat = q.get('category', '其他')
    if cat in categories:
        categories[cat].append(q)

#格式化消息
message = f"""## 芯片产业链每日情报 20260610

### 大盘指数"""

for idx in indices:
    emoji = "📈" if idx.get('change_pct', 0) >= 0 else "📉"
    message += f"\n{emoji} *{idx.get('name')}*: {idx.get('price'):.2f} ({idx.get('change_pct'):+.2f}%)"

message += "\n\n### 产业链详情 (网页版)"

for cat_name, stocks in categories.items():
    if stocks:
        message += f"\n\n**{cat_name}** ({len(stocks)}只)"
        for s in stocks[:3]:  # 每类最多显示3只
            detail = get_stock_detail(s.get('code', ''))
            change = s.get('change_pct', 0)
            emoji = "✅" if change >= 0 else "❌"
            message += f"\n{emoji} {detail.get('name', s.get('code'))}: {change:+.2f}%"

if len(stocks) > 3:
    message += f"\n... 等{cat_name}共{len(stocks)}只"

message += """

---
📄 **完整报告(HTML)**: `data/supply_chain_reports/20260610/daily_digest.html`
包含：产业链位置、主要业务、研报来源

生成时间: """ + datetime.now().strftime('%H:%M:%S')

# 发送
config = load_webhook_config()
notifier = WeChatNotifier(config['wechat_url'])
result = notifier.send(message)
print('发送结果:', '成功' if result else '失败')