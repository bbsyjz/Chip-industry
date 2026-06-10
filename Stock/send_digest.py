import json
from pathlib import Path
from webhook_notifier import WeChatNotifier, load_webhook_config
from datetime import datetime

# 加载数据
with open('data/daily_quotes/20260610/quotes.json', 'r') as f:
    data = json.load(f)

quotes = data.get('quotes', [])
indices = data.get('market_indices', [])

sorted_quotes = sorted(quotes, key=lambda x: x.get('change_pct', 0), reverse=True)
top_gainers = sorted_quotes[:5]
top_losers = [q for q in sorted_quotes[-5:] if q.get('change_pct', 0) > -50]  # 过滤异常值

# 格式化消息
message = f"""## 芯片产业链每日情报 20260610

### 大盘指数"""

for idx in indices:
    emoji = "📈" if idx.get('change_pct', 0) >= 0 else "📉"
    message += f"\n{emoji} *{idx.get('name')}*: {idx.get('price'):.2f} ({idx.get('change_pct'):+.2f}%)"

message += "\n\n### 涨幅TOP5"
for q in top_gainers:
    message += f"\n✅ {q.get('name')}({q.get('code')}): {q.get('change_pct'):+.2f}%"

if top_losers:
    message += "\n\n### 跌幅TOP5"
    for q in top_losers:
        message += f"\n❌ {q.get('name')}({q.get('code')}): {q.get('change_pct'):+.2f}%"

message += f"\n\n---\n生成时间: {datetime.now().strftime('%H:%M:%S')}\n数据来源: 新浪财经"

# 发送
config = load_webhook_config()
notifier = WeChatNotifier(config['wechat_url'])
result = notifier.send(message)
print('发送结果:', '成功' if result else '失败')