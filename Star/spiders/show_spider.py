import requests
from config import BASE_HEADERS

def fetch_damai_concert(city:str, artist_name:str=""):
    concert_list = []
    url = f"https://search.damai.cn/searchajax.html?keyword={artist_name}&city={city}"
    try:
        res = requests.get(url, headers=BASE_HEADERS, timeout=10)
        data = res.json()
        items = data.get("data",{}).get("list",[])
        for item in items:
            concert_list.append({
                "show_name":item.get("name",""),
                "venue":item.get("venue",""),
                "show_time":item.get("show_time",""),
                "price_range":item.get("price","")
            })
    except:
        pass
    return concert_list
