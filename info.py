import requests
import time
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别为 DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("app_log.log", mode='a')  # 输出到日志文件
    ]
)

# 定义请求的 URL
url = "https://chintai.r6.ur-net.go.jp/chintai/api/bukken/search/map_window/"

# 定义请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

# 假设 location_map 是包含多个 id 的列表
location_map = [
    "50_1820",  # 川口芝園
    # "20_2160",  # 江北六丁目 这个位置现在被注释掉了
    "50_4040",  # シティコート川口
    "50_2890",  # リプレ川口二番街
    "50_3890",  # コンフォール川口飯塚
    "50_3040",  # アーバンハイツ飯塚三丁目
    "50_2580",  # 飯塚四丁目ハイツ
]

# 用于存储所有地点信息
all_info = []

def query_and_send_info():
    """
    查询所有地点信息并发送到 Discord，仅当房产信息中 'room' 数据不为空时。
    """
    global all_info
    all_info = []

    for location_id in location_map:
        payload = {
            "rent_low": None,
            "rent_high": None,
            "floorspace_low": None,
            "floorspace_high": None,
            "id": location_id
        }

        try:
            logging.info(f"正在请求地点 ID: {location_id} ...")
            response = requests.post(url, headers=headers, data=payload)

            logging.debug(f"请求 {location_id} 的响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                location_name = data.get('name')
                shop_name = data.get('shopName')
                shop_phone = data.get('shopNum')

                rooms_info = []
                if 'room' in data and data['room']:
                    logging.info(f"地点 {location_name} 有 {len(data['room'])} 间房间信息。")
                    for room in data['room']:
                        rooms_info.append({
                            "room_name": room.get('name'),
                            "room_type": room.get('type'),
                            "room_rent": room.get('rent'),
                            "room_commonfee": room.get('commonfee'),
                            "room_floorspace": room.get('floorspace'),
                            "room_floor": room.get('floor')
                        })

                    all_info.append({
                        "location_name": location_name,
                        "shop_name": shop_name,
                        "shop_phone": shop_phone,
                        "rooms": rooms_info
                    })
                else:
                    logging.info(f"地点 {location_name} 没有房间信息，跳过该地点.")
            else:
                logging.error(f"请求 {location_id} 失败，状态码: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logging.error(f"请求 {location_id} 时发生错误: {e}")
            continue

    if all_info:
        logging.info("有有效的房间信息，开始发送到 Discord.")
        send_discord_message()
    else:
        logging.info("没有有效的房间信息，跳过发送消息.")

def send_discord_message():
    """
    发送房产信息到 Discord。
    """
    fields = []
    for info in all_info:
        rooms_details = ""
        for room in info['rooms']:
            rooms_details += f"房间名: {room['room_name']}\n房间类型: {room['room_type']}\n租金: {room['room_rent']}\n共益费: {room['room_commonfee']}\n面积: {room['room_floorspace']}\n楼层: {room['room_floor']}\n\n"

        fields.append({
            "name": f"地址: {info['location_name']}",
            "value": f"商店名称: {info['shop_name']}\n电话号码: {info['shop_phone']}\n\n房间信息:\n{rooms_details}",
            "inline": False
        })

    WEBHOOK_URL = "https://discord.com/api/webhooks/1338332106694070324/nl4vTcwXLC53MPlh0qjbknHjhzvMxEVpsFvLWvggPWTRJQZrFWkKVjjAUTbVl1kKeB-z"
    embed = {
        "title": "团地信息",
        "description": "以下是查询到的商店和房间信息",
        "color": 16711680,  # 红色
        "fields": fields
    }

    data = {
        "username": "MyBot",
        "embeds": [embed]
    }

    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code in [200, 204]:
        logging.info("消息成功发送到 Discord.")
    else:
        logging.error(f"消息发送失败，状态码: {response.status_code}")

# 每天发送运行状态
status_sent_today = False

def send_daily_status():
    """
    每天中午 12:00 发送程序运行状态。
    """
    global status_sent_today

    current_time = time.localtime()
    if current_time.tm_hour == 12 and not status_sent_today:
        WEBHOOK_URL = "https://discord.com/api/webhooks/1338332106694070324/nl4vTcwXLC53MPlh0qjbknHjhzvMxEVpsFvLWvggPWTRJQZrFWkKVjjAUTbVl1kKeB-z"
        embed = {
            "title": "程序运行状态",
            "description": "程序正在正常运行。",
            "color": 65280  # 绿色
        }

        data = {
            "username": "MyBot",
            "embeds": [embed]
        }

        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code in [200, 204]:
            logging.info("每日状态报告成功发送到 Discord.")
            status_sent_today = True
        else:
            logging.error(f"每日状态报告发送失败，状态码: {response.status_code}")
    elif current_time.tm_hour != 12:
        status_sent_today = False  # 重置状态，准备下一天发送

# 运行查询和状态发送
while True:
    query_and_send_info()
    send_daily_status()

    logging.info("等待十分钟...")
    time.sleep(600)  # 10 分钟
