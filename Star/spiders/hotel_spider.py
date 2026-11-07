import requests
import time
from config import BASE_HEADERS, SLEEP_SECOND

def fetch_city_hotel(city:str, in_date:str, out_date:str):
    hotel_list = []
    try:
        url = f"https://ihotel.meituan.com/api/hotel/searchList?cityName={city}&checkInDate={in_date}&checkOutDate={out_date}"
        res = requests.get(url, headers=BASE_HEADERS, timeout=12)
        json_data = res.json()
        lists = json_data.get("data",{}).get("hotelList",[])
        for h in lists:
            hotel_list.append({
                "hotel_name": h.get("name",""),
                "address": h.get("address",""),
                "price": h.get("minPrice",""),
                "score": h.get("score",""),
                "distance": h.get("distanceDesc",""),
                "check_in": in_date,
                "check_out": out_date
            })
        time.sleep(SLEEP_SECOND)
    except:
        pass
    return hotel_list
