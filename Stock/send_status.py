from webhook_notifier import WeChatNotifier, load_webhook_config
from datetime import datetime

config = load_webhook_config()
notifier = WeChatNotifier(config['wechat_url'])

date_str = '20260610'
message = f"""## 芯片产业链每日情报 {date_str}

⚠️ **数据采集提示**

今日采集受网络代理影响，部分数据不完整：
- 成功采集: 8只股票
- 失败: 29只股票 (代理连接问题)

### 已采集股票 (示例)
| 代码 | 名称 |
|------|------|
| 601216 | 沪硅产业 |
| 688126 | 上海新昇 |
| 002163 | 彩虹股份 |
| 688981 | 中芯国际 |

### 建议
请稍后手动运行 `python3 chip_workflow.py --collect-only` 重新采集

---
生成时间: {datetime.now().strftime("%H:%M:%S")}
由Claude Code自动生成"""

result = notifier.send(message)
print('发送结果:', '成功' if result else '失败')