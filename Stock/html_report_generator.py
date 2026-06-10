"""
芯片产业链股票详情 - HTML报告生成器
包含：产业链位置、主要业务、研报来源、成交量TOP15
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

STOCK_INFO = {
    "688126": {"name": "沪硅产业", "category": "上游材料", "segment": "硅片", "main_business": "半导体硅片研发、生产与销售", "position": "半导体制造的上游材料供应商", "research_reports": [("华泰证券", "https://www.cls.cn/stock/688126"), ("中金公司", "https://www.cls.cn/stock/688126")]},
    "600707": {"name": "彩虹股份", "category": "上游材料", "segment": "玻璃基板", "main_business": "液晶基板玻璃、盖板玻璃", "position": "LCD面板上游材料", "research_reports": [("光大证券", "https://www.cls.cn/stock/600707")]},
    "000413": {"name": "东旭光电", "category": "上游材料", "segment": "玻璃基板", "main_business": "光电显示器件玻璃基板", "position": "国内最大玻璃基板生产基地", "research_reports": [("兴业证券", "https://www.cls.cn/stock/000413")]},
    "600183": {"name": "生益科技", "category": "上游材料", "segment": "PCB基材", "main_business": "覆铜板、ABF薄膜材料", "position": "国内覆铜板龙头", "research_reports": [("招商证券", "https://www.cls.cn/stock/600183")]},
    "603260": {"name": "合盛硅业", "category": "上游材料", "segment": "电子级多晶硅", "main_business": "工业硅、有机硅", "position": "硅基材料上游供应商", "research_reports": [("中信证券", "https://www.cls.cn/stock/603260")]},
    "301269": {"name": "华大九天", "category": "上游设备", "segment": "EDA工具", "main_business": "EDA软件工具开发", "position": "国内EDA龙头", "research_reports": [("华泰证券", "https://www.cls.cn/stock/301269")]},
    "874883": {"name": "芯愿景", "category": "上游设备", "segment": "EDA工具", "main_business": "集成电路设计服务", "position": "IC分析设计服务商", "research_reports": [("方正证券", "https://www.cls.cn/stock/874883")]},
    "688012": {"name": "中微公司", "category": "上游设备", "segment": "刻蚀设备", "main_business": "等离子刻蚀设备、MOCVD", "position": "半导体制造核心设备", "research_reports": [("招商证券", "https://www.cls.cn/stock/688012")]},
    "002371": {"name": "北方华创", "category": "上游设备", "segment": "薄膜沉积/刻蚀设备", "main_business": "半导体设备", "position": "国内半导体设备龙头", "research_reports": [("华泰证券", "https://www.cls.cn/stock/002371")]},
    "688001": {"name": "华兴源创", "category": "上游设备", "segment": "封装测试设备", "main_business": "检测设备、自动化设备", "position": "面板检测龙头", "research_reports": [("兴业证券", "https://www.cls.cn/stock/688001")]},
    "300751": {"name": "迈为股份", "category": "上游设备", "segment": "封装测试设备", "main_business": "光伏电池丝网印刷设备", "position": "光伏设备龙头", "research_reports": [("中金公司", "https://www.cls.cn/stock/300751")]},
    "688981": {"name": "中芯国际", "category": "中游制造", "segment": "晶圆代工", "main_business": "晶圆代工服务", "position": "国内最大晶圆代工厂", "research_reports": [("中金公司", "https://www.cls.cn/stock/688981")]},
    "000725": {"name": "京东方A", "category": "中游制造", "segment": "面板/半导体", "main_business": "LCD/OLED面板", "position": "全球面板龙头", "research_reports": [("华泰证券", "https://www.cls.cn/stock/000725")]},
    "688256": {"name": "寒武纪", "category": "中游制造", "segment": "IC设计", "main_business": "AI芯片设计", "position": "AI芯片设计龙头", "research_reports": [("国信证券", "https://www.cls.cn/stock/688256")]},
    "688521": {"name": "芯原股份", "category": "中游制造", "segment": "IC设计", "main_business": "芯片设计平台服务", "position": "芯片设计服务龙头", "research_reports": [("兴业证券", "https://www.cls.cn/stock/688521")]},
    "688595": {"name": "芯海科技", "category": "中游制造", "segment": "IC设计", "main_business": "高精度ADC、高性能MCU", "position": "模拟芯片设计", "research_reports": [("华西证券", "https://www.cls.cn/stock/688595")]},
    "603986": {"name": "兆易创新", "category": "中游制造", "segment": "存储芯片", "main_business": "NOR Flash、MCU", "position": "国内存储芯片龙头", "research_reports": [("华泰证券", "https://www.cls.cn/stock/603986")]},
    "688008": {"name": "澜起科技", "category": "中游制造", "segment": "存储芯片", "main_business": "内存接口芯片", "position": "内存接口芯片全球龙头", "research_reports": [("招商证券", "https://www.cls.cn/stock/688008")]},
    "600584": {"name": "长电科技", "category": "中游封装", "segment": "先进封装", "main_business": "芯片封测、CoWoS封装", "position": "全球第三大封测厂", "research_reports": [("华泰证券", "https://www.cls.cn/stock/600584")]},
    "002156": {"name": "通富微电", "category": "中游封装", "segment": "先进封装", "main_business": "集成电路封测", "position": "国内封测龙头", "research_reports": [("招商证券", "https://www.cls.cn/stock/002156")]},
    "002185": {"name": "华天科技", "category": "中游封装", "segment": "先进封装", "main_business": "半导体封测", "position": "国内封测龙头", "research_reports": [("兴业证券", "https://www.cls.cn/stock/002185")]},
    "002916": {"name": "深南电路", "category": "中游封装", "segment": "封装载板", "main_business": "PCB、封装载板", "position": "国内PCB/载板龙头", "research_reports": [("华泰证券", "https://www.cls.cn/stock/002916")]},
    "603186": {"name": "华正新材", "category": "中游封装", "segment": "封装载板", "main_business": "覆铜板、复合材料", "position": "覆铜板材料供应商", "research_reports": [("中泰证券", "https://www.cls.cn/stock/603186")]},
    "000977": {"name": "浪潮信息", "category": "下游应用", "segment": "AI服务器", "main_business": "服务器、存储", "position": "国内服务器龙头", "research_reports": [("华泰证券", "https://www.cls.cn/stock/000977")]},
    "000938": {"name": "紫光股份", "category": "下游应用", "segment": "AI服务器", "main_business": "IT基础设施、云服务", "position": "旗下新华三服务器", "research_reports": [("招商证券", "https://www.cls.cn/stock/000938")]},
    "002837": {"name": "英维克", "category": "下游应用", "segment": "液冷散热", "main_business": "精密温控设备", "position": "数据中心温控龙头", "research_reports": [("华泰证券", "https://www.cls.cn/stock/002837")]},
    "301018": {"name": "申菱环境", "category": "下游应用", "segment": "液冷散热", "main_business": "温控设备、散热系统", "position": "数据中心温控", "research_reports": [("兴业证券", "https://www.cls.cn/stock/301018")]},
    "300866": {"name": "安克创新", "category": "下游应用", "segment": "电源管理", "main_business": "消费电子充电设备", "position": "消费电子配件龙头", "research_reports": [("中金公司", "https://www.cls.cn/stock/300866")]},
    "002463": {"name": "沪电股份", "category": "下游应用", "segment": "半导体材料", "main_business": "PCB、铜箔", "position": "PCB材料供应商", "research_reports": [("方正证券", "https://www.cls.cn/stock/002463")]},
}


def get_stock_detail(code):
    return STOCK_INFO.get(code, {"name": code, "category": "其他", "segment": "其他", "main_business": "数据待完善", "position": "产业链位置待确定", "research_reports": []})


def generate_html_report(date_str, data, output_path):
    indices = data.get('market_indices', [])
    quotes = data.get('quotes', [])

    categories = {"上游材料": [], "上游设备": [], "中游制造": [], "中游封装": [], "下游应用": []}
    for q in quotes:
        cat = q.get('category', '其他')
        if cat in categories:
            categories[cat].append(q)

    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>芯片产业链每日情报""")
    html_parts.append(f" {date_str}</title>")
    html_parts.append(""" <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1b2a; color: #e0e0e0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #00d4ff; margin-bottom: 10px; font-size: 24px; }
        .subtitle { text-align: center; color: #888; margin-bottom: 30px; font-size: 14px; }
        .indices { display: flex; gap: 15px; flex-wrap: wrap; justify-content: center; margin-bottom: 30px; }
        .index-card { background: #1b2838; padding: 15px 25px; border-radius: 10px; text-align: center; min-width: 150px; }
        .index-card .name { color: #888; font-size: 12px; }
        .index-card .price { font-size: 20px; font-weight: bold; color: #fff; margin: 5px 0; }
        .index-card .change { font-size: 14px; }
        .up { color: #76b900; }
        .down { color: #e74c3c; }
        .section { background: #1b2838; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .section-title { color: #00d4ff; font-size: 16px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #2a3f54; }
        .stock-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 15px; }
        .stock-card { background: #152238; border-radius: 8px; padding: 15px; border-left: 3px solid #00d4ff; }
        .stock-card.up { border-left-color: #76b900; }
        .stock-card.down { border-left-color: #e74c3c; }
        .stock-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .stock-name { font-size: 14px; font-weight: bold; color: #fff; }
        .stock-code { font-size: 12px; color: #666; }
        .stock-price { text-align: right; }
        .stock-price .price { font-size: 16px; font-weight: bold; color: #fff; }
        .stock-price .change { font-size: 12px; }
        .stock-detail { font-size: 12px; color: #aaa; line-height: 1.6; }
        .stock-detail .label { color: #00d4ff; width: 70px; display: inline-block; }
        .stock-detail p { margin: 3px 0; }
        .research { margin-top: 10px; padding-top: 10px; border-top: 1px solid #2a3f54; }
        .research a { color: #76b900; font-size: 11px; text-decoration: none; margin-right: 15px; }
        .research a:hover { text-decoration: underline; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #2a3f54; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .data-table th, .data-table td { padding: 10px 8px; text-align: center; border-bottom: 1px solid #2a3f54; font-size: 13px; }
        .data-table th { background: #0d1b2a; color: #00d4ff; font-weight: normal; }
        .data-table tr:hover { background: #1a2d40; }
        .data-table .up { color: #76b900; }
        .data-table .down { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>芯片产业链每日情报</h1>
        <p class="subtitle">""")
    html_parts.append(f"{date_str} | 数据来源：新浪财经</p>")
    html_parts.append("""        <div class="indices">
""")

    for idx in indices:
        change = idx.get('change_pct', 0)
        cls = 'up' if change >= 0 else 'down'
        sign = '+' if change >= 0 else ''
        html_parts.append(f"""            <div class="index-card">
                <div class="name">{idx.get('name', '')}</div>
                <div class="price">{idx.get('price', 0):.2f}</div>
                <div class="change {cls}">{sign}{change:.2f}%</div>
            </div>
""")

    html_parts.append("""        </div>
""")

    category_names = {"上游材料": "上游材料", "上游设备": "上游设备", "中游制造": "中游制造", "中游封装": "中游封装", "下游应用": "下游应用"}

    for cat_name, stocks in categories.items():
        if not stocks:
            continue
        html_parts.append(f"""        <div class="section">
            <h2 class="section-title">{category_names.get(cat_name, cat_name)} ({len(stocks)}只)</h2>
            <div class="stock-grid">
""")
        for s in stocks:
            code = s.get('code', '')
            detail = get_stock_detail(code)
            change = s.get('change_pct', 0)
            cls = 'up' if change >= 0 else 'down'
            sign = '+' if change >= 0 else ''
            reports_html = ""
            for name, url in detail.get('research_reports', []):
                reports_html += f'<a href="{url}" target="_blank">{name}</a> '
            html_parts.append(f"""                <div class="stock-card {cls}">
                    <div class="stock-header">
                        <div>
                            <span class="stock-name">{detail.get('name', code)}</span>
                            <span class="stock-code">{code}</span>
                        </div>
                        <div class="stock-price">
                            <div class="price">{s.get('price', 0):.2f}</div>
                            <div class="change {cls}">{sign}{change:.2f}%</div>
                        </div>
                    </div>
                    <div class="stock-detail">
                        <p><span class="label">细分领域</span>{detail.get('segment', '')}</p>
                        <p><span class="label">产业链位置</span>{detail.get('position', '')}</p>
                        <p><span class="label">主要业务</span>{detail.get('main_business', '')}</p>
                    </div>
                    <div class="research">{reports_html}</div>
                </div>
""")
        html_parts.append("""            </div>
        </div>
""")

    sorted_by_volume = sorted(quotes, key=lambda x: x.get('volume', 0), reverse=True)[:15]
    html_parts.append("""        <div class="section">
            <h2 class="section-title">成交量TOP15</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>股票名称</th>
                        <th>股票代码</th>
                        <th>收盘价(元)</th>
                        <th>涨跌幅</th>
                        <th>成交量(万股)</th>
                        <th>成交额(亿元)</th>
                    </tr>
                </thead>
                <tbody>
""")
    for rank, s in enumerate(sorted_by_volume, 1):
        code = s.get('code', '')
        detail = get_stock_detail(code)
        change = s.get('change_pct', 0)
        volume = s.get('volume', 0) / 10000
        amount = s.get('amount', 0) / 100000000
        cls = 'up' if change >= 0 else 'down'
        sign = '+' if change >= 0 else ''
        html_parts.append(f"""                    <tr>
                        <td>{rank}</td>
                        <td>{detail.get('name', code)}</td>
                        <td>{code}</td>
                        <td>{s.get('price', 0):.2f}</td>
                        <td class="{cls}">{sign}{change:.2f}%</td>
                        <td>{volume:.2f}</td>
                        <td>{amount:.2f}</td>
                    </tr>
""")
    html_parts.append("""                </tbody>
            </table>
        </div>
""")

    html_parts.append(f""" <div class="footer">
            生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            由Claude Code自动生成 | 数据来源：新浪财经
        </div>
    </div>
</body>
</html>
""")

    html = ''.join(html_parts)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML报告已生成: {output_path}")


if __name__ == "__main__":
    from pathlib import Path
    data_file = Path("data/daily_quotes/20260610/quotes.json")
    if data_file.exists():
        with open(data_file) as f:
            data = json.load(f)
        output = Path("data/supply_chain_reports/20260610/daily_digest.html")
        output.parent.mkdir(parents=True, exist_ok=True)
        generate_html_report("20260610", data, str(output))