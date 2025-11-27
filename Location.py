import requests


def get_location_by_ip():
    try:
        headers = {
            "sec-ch-ua": "\"Chromium\";v=\"142\", \"Microsoft Edge\";v=\"142\", \"Not_A Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-encoding": "gzip, deflate, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=0, i"
        }
        response = requests.get('https://api.ip.sb/geoip/',headers=headers)
        # print(response.text)
        data = response.json()
        location_info = {
            'city': data.get('city'),
            'region': data.get('region'),
            'country': data.get('country'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude')
        }
        # print(location_info)
        return location_info
    except Exception as e:
        print(f"获取位置失败: {e}")
        return None


# 调用函数
if __name__ == "__main__":
   # location = get_location_by_ip()
    #if location:
    print(f"当前位置信息:{get_location_by_ip()}")
      #  for key, value in location.items():
    #        print(f"{key}: {value}")
   #else:
        #print("无法获取位置信息")