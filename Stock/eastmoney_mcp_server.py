#!/usr/bin/env python3
"""
东方财富网 MCP Server
提供股票行情、K线数据、财务数据等金融信息服务
"""

import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 东方财富网API基础地址
BASE_URL = "https://push2.eastmoney.com"

# MCP服务器配置
SERVER_NAME = "eastmoney-mcp"
SERVER_VERSION = "1.0.0"

app = Server(SERVER_NAME)


def make_request(url: str, params: dict) -> Optional[dict]:
    """发送请求到东方财富网API"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.eastmoney.com"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"请求失败: {e}")
        return None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="get_stock_quote",
            description="获取股票实时行情数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码，如: 600519 (茅台), 000001 (平安)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_stock_kline",
            description="获取股票K线数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "period": {
                        "type": "string",
                        "description": "K线周期: daily, weekly, monthly, min60, min30, min15, min5",
                        "default": "daily"
                    },
                    "count": {
                        "type": "number",
                        "description": "获取K线数量，默认120根",
                        "default": 120
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="search_stock",
            description="搜索股票信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词（股票代码或名称）"
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="get_financial_report",
            description="获取股票财务报告摘要",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "report_type": {
                        "type": "string",
                        "description": "报告类型: annual(年报), season(季报), half(半年报)",
                        "default": "annual"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_stock_news",
            description="获取股票新闻和公告",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "count": {
                        "type": "number",
                        "description": "获取新闻数量",
                        "default": 10
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_market_quotation",
            description="获取大盘指数行情",
            inputSchema={
                "type": "object",
                "properties": {
                    "indices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "指数代码列表，如: ['sh000001'(上证), 'sz399001'(深证), 'sh000300'(沪深300)]"
                    }
                },
                "required": ["indices"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "get_stock_quote":
            return await get_stock_quote(arguments.get("symbol"))
        elif name == "get_stock_kline":
            return await get_stock_kline(
                arguments.get("symbol"),
                arguments.get("period", "daily"),
                arguments.get("count", 120)
            )
        elif name == "search_stock":
            return await search_stock(arguments.get("keyword"))
        elif name == "get_financial_report":
            return await get_financial_report(
                arguments.get("symbol"),
                arguments.get("report_type", "annual")
            )
        elif name == "get_stock_news":
            return await get_stock_news(
                arguments.get("symbol"),
                arguments.get("count", 10)
            )
        elif name == "get_market_quotation":
            return await get_market_quotation(arguments.get("indices"))
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    except Exception as e:
        logger.error(f"工具调用失败: {e}")
        return [TextContent(type="text", text=f"错误: {str(e)}")]


async def get_stock_quote(symbol: str) -> list[TextContent]:
    """获取股票实时行情"""
    # 转换股票代码格式
    if symbol.startswith("6"):
        secid = f"1.{symbol}"
    else:
        secid = f"0.{symbol}"

    url = f"{BASE_URL}/push股票的实时行情"
    params = {
        "id": secid,
        "fields": "f12,f14,f3,f4,f5,f6,f7,f8,f9,f10,f11,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f33,f36,f37,f38,f39,f40,f41,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58"
    }

    result = make_request(url, params)
    if result and result.get("data"):
        data = result["data"]
        quote_info = {
            "股票代码": data.get("f12", ""),
            "股票名称": data.get("f14", ""),
            "最新价": data.get("f3", ""),
            "涨跌幅": f"{data.get('f4', 0)}%",
            "涨跌额": data.get("f4", ""),
            "成交量": data.get("f5", ""),
            "成交额": data.get("f6", ""),
            "振幅": f"{data.get('f7', 0)}%",
            "换手率": f"{data.get('f8', 0)}%",
            "市盈率": data.get("f9", ""),
            "市净率": data.get("f10", ""),
            "总市值": data.get("f20", ""),
            "流通市值": data.get("f21", "")
        }
        return [TextContent(type="text", text=json.dumps(quote_info, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text="未获取到行情数据")]


async def get_stock_kline(symbol: str, period: str = "daily", count: int = 120) -> list[TextContent]:
    """获取股票K线数据"""
    # 转换股票代码格式
    if symbol.startswith("6"):
        secid = f"1.{symbol}"
    else:
        secid = f"0.{symbol}"

    # 转换周期参数
    period_map = {
        "daily": "101",
        "weekly": "102",
        "monthly": "103",
        "min60": "60",
        "min30": "30",
        "min15": "15",
        "min5": "5"
    }
    klt = period_map.get(period, "101")
    fqt = "0"  # 不复权

    url = f"{BASE_URL}/api/kline/getkline"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": klt,
        "fqt": fqt,
        "secid": secid,
        "beg": "0",
        "end": str(count)
    }

    result = make_request(url, params)
    if result and result.get("data"):
        klines = result["data"].get("klines", [])
        data_list = []
        for line in klines:
            parts = line.split(",")
            data_list.append({
                "日期": parts[0],
                "开盘": parts[1],
                "收盘": parts[2],
                "最高": parts[3],
                "最低": parts[4],
                "成交量": parts[5],
                "成交额": parts[6],
                "振幅": parts[7] if len(parts) > 7 else "",
                "涨跌幅": parts[8] if len(parts) > 8 else "",
                "涨跌额": parts[9] if len(parts) > 9 else "",
                "换手率": parts[10] if len(parts) > 10 else ""
            })
        return [TextContent(type="text", text=json.dumps(data_list[-count:], ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text="未获取到K线数据")]


async def search_stock(keyword: str) -> list[TextContent]:
    """搜索股票"""
    url = "https://searchapi.eastmoney.com/api/suggest/get"
    params = {
        "input": keyword,
        "type": "14",
        "token": "D43BF722C8E33BDC906FB84D85E326E8",
        "markettype": "",
        "mktnum": "",
        "jys": "",
        "classify": "",
        "securitytype": "",
        "status": "",
        "count": "10"
    }

    result = make_request(url, params)
    if result and result.get("QuotationCodeTable"):
        stocks = result["QuotationCodeTable"]["Data"]
        result_list = []
        for stock in stocks[:10]:
            result_list.append({
                "股票代码": stock.get("Code", ""),
                "股票名称": stock.get("Name", ""),
                "类型": stock.get("MktNum", ""),
                "交易所": stock.get("Jys", "")
            })
        return [TextContent(type="text", text=json.dumps(result_list, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text="未找到相关股票")]


async def get_financial_report(symbol: str, report_type: str = "annual") -> list[TextContent]:
    """获取财务报告"""
    # 转换股票代码格式
    if symbol.startswith("6"):
        secid = f"1.{symbol}"
    else:
        secid = f"0.{symbol}"

    url = f"{BASE_URL}/api/f10/getfinancialreport"
    params = {
        "secid": secid,
        "type": report_type,
        "count": "4"
    }

    result = make_request(url, params)
    if result:
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text="未获取到财务报告")]


async def get_stock_news(symbol: str, count: int = 10) -> list[TextContent]:
    """获取股票新闻公告"""
    url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
    params = {
        "sr": "-1",
        "page_size": count,
        "page_index": "1",
        "ann_type": "ALL",
        "stock_code": symbol
    }

    result = make_request(url, params)
    if result and result.get("data"):
        notices = result["data"]["list"]
        result_list = []
        for notice in notices:
            result_list.append({
                "标题": notice.get("title", ""),
                "发布时间": notice.get("notice_date", ""),
                "类型": notice.get("art_cat", ""),
                "链接": f"https://np-anotice-stock.eastmoney.com/{notice.get('art_id', '')}"
            })
        return [TextContent(type="text", text=json.dumps(result_list, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text="未获取到新闻公告")]


async def get_market_quotation(indices: list) -> list[TextContent]:
    """获取大盘指数"""
    secids = []
    for idx in indices:
        if idx.startswith("sh"):
            secids.append(f"1.{idx[2:]}")
        elif idx.startswith("sz"):
            secids.append(f"0.{idx[2:]}")

    url = f"{BASE_URL}/push_batch_stock_quotes"
    params = {
        "ids": ",".join(secids),
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14"
    }

    result = make_request(url, params)
    if result and result.get("data"):
        quotes = result["data"]
        result_list = []
        for quote in quotes:
            result_list.append({
                "指数代码": quote.get("f12", ""),
                "指数名称": quote.get("f14", ""),
                "最新点位": quote.get("f2", ""),
                "涨跌幅": f"{quote.get('f3', 0)}%",
                "涨跌额": quote.get("f4", ""),
                "成交量": quote.get("f5", ""),
                "成交额": quote.get("f6", "")
            })
        return [TextContent(type="text", text=json.dumps(result_list, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text="未获取到指数数据")]


async def main():
    """启动MCP服务器"""
    logger.info(f"启动 {SERVER_NAME} v{SERVER_VERSION}")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())