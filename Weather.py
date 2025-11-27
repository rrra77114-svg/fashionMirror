import requests
import json

def get_location():
    try:
        response = requests.get('https://ipapi.co/json/')
        data = response.json()
        location_info = {
            'city': data.get('city'),
            'region': data.get('region'),
            'country': data.get('country_name'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude')
        }
        return location_info
    except Exception as e:
        print(f"获取位置失败: {e}")
        return None

def get_current_weather():
    """
    获取当前位置的简单天气信息

    返回格式:
    {

        "temperature": "当前温度 (℃)",
        "feels_like": "体感温度 (℃)",
        "weather": "天气描述",
        "humidity": "湿度 (%)",
        "wind_speed": "风速 (米/秒)"
    }
    """


    # 2. 获取天气信息
    def get_weather(lat, lon):
        """使用经纬度获取天气信息"""
        try:
            # 替换为你的OpenWeatherMap API密钥
            API_KEY = "d92f641c9b5e73eb5ee359ebf2716f83"
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=zh_cn"

            response = requests.get(url, timeout=5)
            #print(response.json())
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    # 3. 主逻辑
    try:
        # 获取当前位置
        location = get_location()
        if not location:
            return {"error": "无法获取当前位置信息"}

        # 获取天气数据
        weather_data = get_weather(location['latitude'], location['longitude'])
        if not weather_data:
            return {"error": "无法获取天气信息"}

        # 提取并格式化天气信息
        return {
            "temperature": f"{weather_data['main']['temp']:.1f}℃",
            "feels_like": f"{weather_data['main']['feels_like']:.1f}℃",
            "weather": weather_data['weather'][0]['description'],
            "humidity": f"{weather_data['main']['humidity']}%",
            "wind_speed": f"{weather_data['wind']['speed']} m/s"
        }

    except Exception as e:
        return {"error": f"获取天气信息失败: {str(e)}"}


# 使用示例
if __name__ == "__main__":
    weather = get_current_weather()
    print(weather)
    if 'error' in weather:
        print(f"错误: {weather['error']}")
    else:
        print("=" * 40)
        print(f"当前温度: {weather['temperature']}")
        print(f"体感温度: {weather['feels_like']}")
        print(f"天气状况: {weather['weather']}")
        print(f"湿度: {weather['humidity']}")
        print(f"风速: {weather['wind_speed']}")
        print("=" * 40)