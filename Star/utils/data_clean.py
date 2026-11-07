from datetime import datetime, timedelta

def clean_all_traffic_data(train_list, flight_list, concert_list, back_train=[], back_flight=[], hotel_list=[]):
    data = {
        "concert_info": concert_list,
        "go_train": train_list,
        "go_flight": flight_list,
        "back_train": back_train,
        "back_flight": back_flight,
        "hotel_info": hotel_list
    }
    return data

# 生成前后区间日期
def get_date_range(base_date: str, offset: int):
    date_list = []
    base = datetime.strptime(base_date, "%Y-%m-%d")
    target = base + timedelta(days=offset)
    return target.strftime("%Y-%m-%d")
