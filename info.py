import requests

WEBHOOK_URL = "https://discord.com/api/webhooks/1338332106694070324/nl4vTcwXLC53MPlh0qjbknHjhzvMxEVpsFvLWvggPWTRJQZrFWkKVjjAUTbVl1kKeB-z"

embed = {
    "title": "新团地出现",
    "description": "网址信息：",
    "color": 16711680,  # 0xFF0000（红色）
}

data = {
    "username": "MyBot",
    "embeds": [embed]
}

response = requests.post(WEBHOOK_URL, json=data)
print(response.status_code)  # 200 表示成功
