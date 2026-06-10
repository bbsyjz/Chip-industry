"""
芯片产业链股票池配置 - 修正版
按英伟达GTC技术架构分层
"""

CHIP_SUPPLY_CHAIN = {
    # 上游材料
    "上游材料": {
        "硅片": [
            {"code": "688126", "name": "沪硅产业"},
        ],
        "玻璃基板": [
            {"code": "600707", "name": "彩虹股份"},
            {"code": "000413", "name": "东旭光电"},
        ],
        "PCB基材": [
            {"code": "600183", "name": "生益科技"},
            {"code": "002916", "name": "深南电路"},
        ],
        "电子级多晶硅": [
            {"code": "603260", "name": "合盛硅业"},
        ],
    },
    # 上游设备
    "上游设备": {
        "EDA工具": [
            {"code": "301269", "name": "华大九天"},
            {"code": "874883", "name": "芯愿景"},
        ],
        "光刻机/刻蚀机": [
            {"code": "688012", "name": "中微公司"},
            {"code": "002371", "name": "北方华创"},
        ],
        "薄膜沉积设备": [
            {"code": "688012", "name": "中微公司"},
            {"code": "002371", "name": "北方华创"},
        ],
        "封装测试设备": [
            {"code": "688001", "name": "华兴源创"},
            {"code": "300751", "name": "迈为股份"},
        ],
    },
    # 中游制造
    "中游制造": {
        "晶圆代工": [
            {"code": "688981", "name": "中芯国际"},
            {"code": "000725", "name": "京东方A"},
        ],
        "IC设计": [
            {"code": "688256", "name": "寒武纪"},
            {"code": "688521", "name": "芯原股份"},
            {"code": "688595", "name": "芯海科技"},
        ],
        "存储芯片": [
            {"code": "603986", "name": "兆易创新"},
            {"code": "688008", "name": "澜起科技"},
        ],
    },
    # 中游封装
    "中游封装": {
        "先进封装(CoWoS)": [
            {"code": "600584", "name": "长电科技"},
            {"code": "002156", "name": "通富微电"},
            {"code": "002185", "name": "华天科技"},
        ],
        "封装载板": [
            {"code": "002916", "name": "深南电路"},
            {"code": "603186", "name": "华正新材"},
        ],
        "ABF薄膜": [
            {"code": "600183", "name": "生益科技"},
        ],
    },
    # 下游应用
    "下游应用": {
        "AI服务器": [
            {"code": "000977", "name": "浪潮信息"},
            {"code": "000938", "name": "紫光股份"},
        ],
        "液冷散热": [
            {"code": "002837", "name": "英维克"},
            {"code": "301018", "name": "申菱环境"},
        ],
        "电源管理": [
            {"code": "300866", "name": "安克创新"},
        ],
        "PCB板": [
            {"code": "002916", "name": "深南电路"},
            {"code": "600183", "name": "生益科技"},
        ],
        "半导体材料": [
            {"code": "002463", "name": "沪电股份"},
        ],
    },
}

# 产业链层级映射
LAYER_MAPPING = {
    "上游材料": "layer_1",
    "上游设备": "layer_1",
    "中游制造": "layer_2",
    "中游封装": "layer_2",
    "下游应用": "layer_3",
}

def get_all_codes():
    codes = []
    for category, segments in CHIP_SUPPLY_CHAIN.items():
        for segment, stocks in segments.items():
            for stock in stocks:
                codes.append(stock["code"])
    return list(set(codes))

def get_all_stocks():
    stocks = []
    for category, segments in CHIP_SUPPLY_CHAIN.items():
        for segment, stock_list in segments.items():
            for stock in stock_list:
                stock_copy = stock.copy()
                stock_copy["category"] = category
                stock_copy["segment"] = segment
                stocks.append(stock_copy)
    return stocks

def get_stocks_by_category(category):
    if category not in CHIP_SUPPLY_CHAIN:
        return []
    stocks = []
    for segment, stock_list in CHIP_SUPPLY_CHAIN[category].items():
        for stock in stock_list:
            stock_copy = stock.copy()
            stock_copy["category"] = category
            stock_copy["segment"] = segment
            stocks.append(stock_copy)
    return stocks

MARKET_INDICES = [
    {"code": "sh000001", "name": "上证指数"},
    {"code": "sz399001", "name": "深证成指"},
    {"code": "sh000300", "name": "沪深300"},
    {"code": "sz399006", "name": "创业板指"},
]

INDEX_CODES = [idx["code"] for idx in MARKET_INDICES]