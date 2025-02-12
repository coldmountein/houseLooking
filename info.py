import requests
import time
import logging
import schedule
import datetime

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别为 DEBUG，输出所有信息
    format='%(asctime)s - %(levelname)s - %(message)s',  # 设置日志格式
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("app_log.log", mode='a')  # 输出到日志文件，追加模式
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

def send_discord_message(webhook_url, title, description, fields, username="MyBot"):
    """
    发送嵌入消息到 Discord Webhook
    """
    embed = {
        "title": title,
        "description": description,
        "color": 16711680,  # 红色
        "fields": fields
    }

    data = {
        "username": username,
        "embeds": [embed]
    }

    response = requests.post(webhook_url, json=data)

    if response.status_code in [200, 204]:
        logging.info("消息成功发送到 Discord.")
    else:
        logging.error(f"消息发送失败，状态码: {response.status_code}")

def query_and_send_info():
    """
    查询所有地点信息并发送到 Discord，仅当房产信息中 'room' 数据不为空时。
    """
    global all_info
    all_info = []  # 每次查询前清空之前的数据

    for location_id in location_map:
        payload = {
            "rent_low": None,
            "rent_high": None,
            "floorspace_low": None,
            "floorspace_high": None,
            "id": location_id
        }

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

    if all_info:
        logging.info("有有效的房间信息，开始发送到 Discord.")
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
        send_discord_message(WEBHOOK_URL, "团地信息", "以下是查询到的商店和房间信息", fields)
    else:
        logging.info("没有有效的房间信息，跳过发送消息.")

def send_daily_report():
    """
    发送程序运行状态的报告到 Discord。
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_message = f"程序运行状态报告：\n当前时间：{current_time}\n程序正在正常运行中。"
    fields = [{
        "name": "程序状态报告",
        "value": report_message,
        "inline": False
    }]

    WEBHOOK_URL = "https://discord.com/api/webhooks/1338332106694070324/nl4vTcwXLC53MPlh0qjbknHjhzvMxEVpsFvLWvggPWTRJQZrFWkKVjjAUTbVl1kKeB-z"
    send_discord_message(WEBHOOK_URL, "每日运行状态报告", "程序当前状态：", fields)

# 每天早上 9 点发送状态报告
schedule.every().day.at("12:00").do(send_daily_report)

# 每十分钟执行一次查询和发送操作
while True:
    query_and_send_info()
    logging.info("等待十分钟...")
    time.sleep(600)  # 等待 600 秒，即 10 分钟

    # 检查并运行每天的任务
    schedule.run_pending()
