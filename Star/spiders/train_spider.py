import requests
import re
import time
from config import BASE_HEADERS, SLEEP_SECOND

def get_all_station_code() -> dict:
    url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
    res = requests.get(url, headers=BASE_HEADERS, timeout=10)
    pattern = r'@([^|]+)\|([A-Z]+)\|'
    result = re.findall(pattern, res.text)
    return {name:code for name,code in result}

def fetch_train_real_data(from_city:str, to_city:str, train_date:str):
    station_map = get_all_station_code()
    from_code = station_map.get(from_city)
    to_code = station_map.get(to_city)
    if not from_code or not to_code:
        return []

    query_url = "https://kyfw.12306.cn/otn/leftTicket/queryA"
    params = {
        "leftTicketDTO.train_date": train_date,
        "leftTicketDTO.from_station": from_code,
        "leftTicketDTO.to_station": to_code,
        "purpose_codes": "ADULT"
    }
    resp = requests.get(query_url, params=params, headers=BASE_HEADERS, timeout=10)
    json_data = resp.json()
    raw_list = json_data.get("data",{}).get("result",[])
    clean_train = []

    for item in raw_list:
        arr = item.split("|")
        if len(arr)<12:
            continue
        train_no = arr[2]
        train_name = arr[3]
        start_time = arr[8]
        end_time = arr[9]
        duration = arr[10]

        price_params = {
            "leftTicketDTO.train_date": train_date,
            "leftTicketDTO.from_station": from_code,
            "leftTicketDTO.to_station": to_code,
            "leftTicketDTO.train_no": train_no,
            "leftTicketDTO.ticket_type": 1
        }
        price_res = requests.get("https://kyfw.12306.cn/otn/leftTicketPrice/query",params=price_params,headers=BASE_HEADERS)
        price_info = price_res.json().get("data",{}).get("priceList",[])
        price_dict = {p["seatType"]:p["price"] for p in price_info}

        clean_train.append({
            "train_name":train_name,
            "start_time":start_time,
            "end_time":end_time,
            "run_time":duration,
            "price":price_dict
        })
        time.sleep(SLEEP_SECOND)
    return clean_train
