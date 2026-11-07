# spiders/flight_spider.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 全局无头浏览器（服务器后台运行不弹窗口）
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(8)
    return driver

def fetch_flight_real_data(dep_city: str, arr_city: str, fly_date: str):
    flight_list = []
    try:
        driver = get_driver()
        driver.get("https://flights.ctrip.com/")
        time.sleep(1.5)

        # 清空并输入出发城市
        dep_input = driver.find_element(By.ID, "DepartureCity")
        dep_input.clear()
        dep_input.send_keys(dep_city)
        time.sleep(1)

        # 清空并输入到达城市
        arr_input = driver.find_element(By.ID, "ArrivalCity")
        arr_input.clear()
        arr_input.send_keys(arr_city)
        time.sleep(1)

        # 输入日期
        date_input = driver.find_element(By.ID, "DepartureDate")
        date_input.clear()
        date_input.send_keys(fly_date)
        time.sleep(1)

        # 点击搜索
        driver.find_element(By.ID, "btnSearch").click()
        time.sleep(6)

        # 解析航班数据
        items = driver.find_elements(By.CLASS_NAME, "flight-item")
        for item in items:
            try:
                flight_no = item.find_element(By.CLASS_NAME, "flight-no").text.strip()
                dep_time = item.find_element(By.CLASS_NAME, "dep-time").text.strip()
                arr_time = item.find_element(By.CLASS_NAME, "arr-time").text.strip()
                price = item.find_element(By.CLASS_NAME, "price").text.strip()

                flight_list.append({
                    "flight_no": flight_no,
                    "dep_time": dep_time,
                    "arr_time": arr_time,
                    "price": price
                })
            except:
                continue
        driver.quit()
    except Exception as e:
        pass
    return flight_list
