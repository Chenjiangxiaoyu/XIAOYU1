from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import requests

# 导入配置与工具
from config import BASE_HEADERS, AI_API_KEY, AI_API_URL
from utils.data_clean import clean_all_traffic_data, get_date_range

# 导入所有爬虫
from spiders.train_spider import fetch_train_real_data
from spiders.show_spider import fetch_damai_concert
from spiders.flight_spider import fetch_flight_real_data
from spiders.hotel_spider import fetch_city_hotel

app = FastAPI(title="追星行程规划系统")

# 挂载静态页面
app.mount("/static", StaticFiles(directory="static"), name="static")

# 全局彻底禁用所有缓存
@app.middleware("http")
async def no_cache_all(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

# 首页路由
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html","r",encoding="utf-8") as f:
        return f.read()

# AI调用函数
async def create_ai_trip(user_info, traffic_data):
    prompt = f"""
你是专业追星出行规划师，所有数据均为**实时当场抓取**，无任何缓存、无过期数据。
用户出行需求：
出发城市：{user_info['start_city']}
演出城市：{user_info['target_city']}
演唱会日期：{user_info['show_date']}
提前出行天数：{user_info['before_days']}
延后返程天数：{user_info['after_days']}
出行风格偏好：{user_info['user_prefer']}
整体出行预算：{user_info['budget']}

当前实时全部数据：
1. 当地演唱会场次信息：{traffic_data['concert_info']}
2. 去程高铁实时车次与票价：{traffic_data['go_train']}
3. 去程实时航班信息：{traffic_data['go_flight']}
4. 返程高铁实时车次：{traffic_data['back_train']}
5. 目的地实时酒店（价格、评分、距离场馆远近）：{traffic_data['hotel_info']}

严格输出要求：
1. 自动匹配入住退房时间，优先推荐离演出场馆近、出行方便的酒店
2. 规划三套完整方案：经济性价比方案、省时快捷方案、舒适省心方案
3. 每套方案写清：出发交通、到达时间、入住酒店、观演安排、返程交通
4. 标注所有实时票价、酒店房价、全程合计花费
5. 提醒入场时间、散场出行注意事项
6. 语言通顺清晰，适合粉丝直接照着出行
7. 结尾统一备注：所有票务、酒店价格为实时抓取，最终以官方平台实际价格为准
"""
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model":"deepseek-chat",
        "messages":[{"role":"user","content":prompt}]
    }
    res = requests.post(AI_API_URL, json=body, headers=headers, timeout=30)
    return res.json()["choices"][0]["message"]["content"]

# 核心接口
@app.post("/api/star-trip")
async def make_trip(req:dict):
    start_city = req["start_city"]
    target_city = req["target_city"]
    show_date = req["show_date"]
    aft_day = req["after_days"]

    # 自动计算酒店入住退房
    check_in = get_date_range(show_date, -1)
    check_out = get_date_range(show_date, aft_day)

    # 实时抓取全部数据
    concert = fetch_damai_concert(target_city)
    go_train = fetch_train_real_data(start_city, target_city, show_date)
    go_flight = fetch_flight_real_data(start_city, target_city, show_date)
    hotel = fetch_city_hotel(target_city, check_in, check_out)

    # 抓取返程火车
    back_train = fetch_train_real_data(target_city, start_city, check_out)

    # 统一清洗数据
    all_data = clean_all_traffic_data(go_train,go_flight,concert,back_train,[],hotel)
    # AI生成行程
    result = await create_ai_trip(req, all_data)
    return {"code":200,"trip_plan":result}
