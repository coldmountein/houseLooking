import requests
import time
import logging

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
    # 可以继续添加其他 id
]

# 用于存储所有地点信息
all_info = []

def query_and_send_info():
    """
    查询所有地点信息并发送到 Discord，仅当房产信息中 'room' 数据不为空时。
    """
    # 遍历所有 id，逐个查询
    for location_id in location_map:
        payload = {
            "rent_low": None,
            "rent_high": None,
            "floorspace_low": None,
            "floorspace_high": None,
            "id": location_id
        }

        # 发送 POST 请求
        logging.info(f"正在请求地点 ID: {location_id} ...")
        response = requests.post(url, headers=headers, data=payload)

        # 输出每个请求的响应内容
        logging.debug(f"请求 {location_id} 的响应状态码: {response.status_code}")

        # 处理返回的数据
        if response.status_code == 200:
            data = response.json()  # 解析返回的 JSON 数据
            location_name = data.get('name')  # 获取地点名
            shop_name = data.get('shopName')  # 获取商店名
            shop_phone = data.get('shopNum')  # 获取商店电话号码
            
            rooms_info = []
            # 仅当 'room' 字段不为空时才处理数据
            if 'room' in data and data['room']:  # 如果 'room' 不为空
                logging.info(f"地点 {location_name} 有 {len(data['room'])} 间房间信息。")
                for room in data['room']:
                    room_name = room.get('name')  # 获取房间名
                    room_type = room.get('type')  # 获取房间类型
                    room_rent = room.get('rent')  # 获取房间租金
                    room_commonfee = room.get('commonfee')  # 获取房间共益费
                    room_floorspace = room.get('floorspace')  # 获取房间面积
                    room_floor = room.get('floor')  # 获取房间楼层
                    rooms_info.append({
                        "room_name": room_name,
                        "room_type": room_type,
                        "room_rent": room_rent,
                        "room_commonfee": room_commonfee,
                        "room_floorspace": room_floorspace,
                        "room_floor": room_floor
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

    # 如果所有查询的 'room' 数据都为空，则不会发送 Discord 消息
    if all_info:
        logging.info("有有效的房间信息，开始发送到 Discord.")
        # 构建 Discord 消息内容
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

        # 发送 Discord 消息
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

        # Discord Webhook URL
        WEBHOOK_URL = "https://discord.com/api/webhooks/1338332106694070324/nl4vTcwXLC53MPlh0qjbknHjhzvMxEVpsFvLWvggPWTRJQZrFWkKVjjAUTbVl1kKeB-z"
        send_discord_message(WEBHOOK_URL, "团地信息", "以下是查询到的商店和房间信息", fields)
    else:
        logging.info("没有有效的房间信息，跳过发送消息.")

# 每五分钟执行一次查询和发送操作
while True:
    query_and_send_info()
    logging.info("等待五分钟...")
    time.sleep(300)  # 等待 300 秒，即 5 分钟
