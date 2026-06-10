"""
Webhook通知模块
支持微信/Slack推送
"""

import requests
import logging
from typing import Dict, List, Optional
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Webhook通知基类"""

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    def send(self, message: str) -> bool:
        """发送消息"""
        raise NotImplementedError


class SlackNotifier(WebhookNotifier):
    """Slack通知"""

    def send(self, message: str, username: str = "Chip Bot") -> bool:
        """发送Slack消息"""
        if not self.webhook_url:
            logger.error("Slack webhook URL未配置")
            return False

        payload = {
            "username": username,
            "text": message,
            "icon_emoji": ":chip:"
        }

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Slack消息发送成功")
                return True
            else:
                logger.error(f"Slack发送失败: {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"Slack发送异常: {e}")
            return False

    def send_file(self, file_path: str, filename: str = None) -> bool:
        """发送文件到Slack (通过文件上传API)"""
        if not self.webhook_url:
            logger.error("Slack webhook URL未配置")
            return False

        # Slack文件上传需要使用files.getUploadURLExternal等API
        # 这里简化处理，只发送文件路径消息
        message = f"报告已生成: {file_path}"
        return self.send(message)


class WeChatNotifier(WebhookNotifier):
    """企业微信通知"""

    def send(self, message: str,mentions: List[str] = None) -> bool:
        """发送企业微信消息"""
        if not self.webhook_url:
            logger.error("企业微信webhook URL未配置")
            return False

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": message
            }
        }

        # 添加提及
        if mentions:
            mentioned_list = []
            for mention in mentions:
                mentioned_list.append(f"<@{mention}>")
            payload["markdown"]["mentioned_list"] = mentioned_list

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info("企业微信消息发送成功")
                    return True
                else:
                    logger.error(f"企业微信发送失败: {result.get('errmsg')}")
                    return False
            else:
                logger.error(f"企业微信HTTP错误: {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"企业微信发送异常: {e}")
            return False

    def send_text(self, content: str) -> bool:
        """发送文本消息"""
        if not self.webhook_url:
            logger.error("企业微信webhook URL未配置")
            return False

        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info("企业微信文本消息发送成功")
                    return True
            return False
        except Exception as e:
            logger.error(f"企业微信发送异常: {e}")
            return False


class CompositeNotifier:
    """复合通知器 - 同时发送到多个渠道"""

    def __init__(self):
        self.notifiers: List[WebhookNotifier] = []

    def add_notifier(self, notifier: WebhookNotifier):
        """添加通知器"""
        self.notifiers.append(notifier)

    def send_all(self, message: str) -> Dict[str, bool]:
        """发送到所有渠道"""
        results = {}
        for notifier in self.notifiers:
            name = notifier.__class__.__name__
            results[name] = notifier.send(message)
        return results


def format_daily_digest_message(date_str: str, data: dict) -> str:
    """格式化每日情报消息"""
    market_indices = data.get('market_indices', [])
    quotes = data.get('quotes', [])

    # 构建消息
    lines = [
        f"## 芯片产业链每日情报 {date_str}",
        "",
        "### 市场概览",
    ]

    for idx in market_indices:
        change = idx.get('change_pct', 0)
        emoji = "📈" if change >= 0 else "📉"
        lines.append(f"{emoji} *{idx.get('name', '')}*: {idx.get('price', 0):.2f} ({change:+.2f}%)")

    # 涨跌排行
    sorted_quotes = sorted(quotes, key=lambda x: x.get('change_pct', 0), reverse=True)
    top_gainers = sorted_quotes[:3]
    top_losers = sorted_quotes[-3:] if len(sorted_quotes) >= 3 else []

    lines.extend(["", "### 涨幅TOP3"])

    for q in top_gainers:
        lines.append(f"✅ {q.get('name', '')}({q.get('code', '')}): {q.get('change_pct', 0):+.2f}%")

    if top_losers:
        lines.extend(["", "### 跌幅TOP3"])
        for q in top_losers:
            lines.append(f"❌ {q.get('name', '')}({q.get('code', '')}): {q.get('change_pct', 0):+.2f}%")

    # 情绪指数
    lines.extend(["", "### 产业链情绪"])
    categories = ["上游材料", "上游设备", "中游制造", "中游封装", "下游应用"]
    for cat in categories:
        cat_quotes = [q for q in quotes if q.get('category') == cat]
        if cat_quotes:
            changes = [q.get('change_pct', 0) for q in cat_quotes]
            avg = sum(changes) / len(changes) if changes else 0
            emoji = "🟢" if avg >= 0 else "🔴"
            lines.append(f"{emoji} {cat}: {avg:+.2f}%")

    lines.extend(["", "---", "由Claude Code自动生成"])

    return "\n".join(lines)


def load_webhook_config(config_path: str = None) -> dict:
    """加载Webhook配置"""
    if config_path is None:
        config_path = Path(__file__).parent / "webhook_config.json"

    if Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def create_notifier_from_config(config: dict = None) -> CompositeNotifier:
    """从配置创建通知器"""
    if config is None:
        config = load_webhook_config()

    composite = CompositeNotifier()

    if config.get("slack_url"):
        composite.add_notifier(SlackNotifier(config["slack_url"]))

    if config.get("wechat_url"):
        composite.add_notifier(WeChatNotifier(config["wechat_url"]))

    return composite


if __name__ == "__main__":
    # 测试
    test_data = {
        "market_indices": [
            {"name": "上证指数", "price": 3300.25, "change_pct": 1.25},
            {"name": "深证成指", "price": 10500.50, "change_pct": 0.85},
        ],
        "quotes": [
            {"code": "688981", "name": "中芯国际", "change_pct": 2.15, "category": "中游制造"},
            {"code": "002916", "name": "深南电路", "change_pct": 5.25, "category": "中游封装"},
        ]
    }

    message = format_daily_digest_message("20250610", test_data)
    print(message)
    print("\n--- 测试通知发送 ---")
    notifier = create_notifier_from_config()
    if notifier.notifiers:
        result = notifier.send_all(message)
        print(f"发送结果: {result}")
    else:
        print("未配置任何webhook，跳过发送测试")