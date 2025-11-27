"""
树莓派5人像检测与穿衣夸夸程序
使用rpicam库调用摄像头，检测人像后上传到豆包API生成夸夸文本
再通过火山TTS转换为语音输出
"""

import cv2
import numpy as np
import requests
import json
import base64
import time
import pygame
import io
import logging
import threading
from datetime import datetime
from deepface import DeepFace
from picamera2 import Picamera2, MappedArray
from libcamera import Transform
from threading import Thread, Lock
from collections import deque

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StreamAudioPlayer:
    def __init__(self, sample_rate=4000):
        self.sample_rate = sample_rate
        self.audio_queue = deque()
        self.is_playing = False
        self.play_thread = None
        pygame.mixer.init(frequency=sample_rate)
    
    def add_audio_chunk(self, audio_data):
        """添加音频数据块到队列"""
        self.audio_queue.append(audio_data)
        if not self.is_playing:
            self.start_playback()
    
    def start_playback(self):
        """开始播放音频"""
        if self.play_thread is None or not self.play_thread.is_alive():
            self.play_thread = threading.Thread(target=self._playback_worker)
            self.play_thread.daemon = True
            self.play_thread.start()
    
    def _playback_worker(self):
        """音频播放工作线程"""
        self.is_playing = True
        try:
            while self.audio_queue or self.is_playing:
                if self.audio_queue:
                    audio_data = self.audio_queue.popleft()
                    
                    # 创建临时内存文件来播放音频
                    audio_buffer = io.BytesIO(audio_data)
                    try:
                        sound = pygame.mixer.Sound(audio_buffer)
                        sound.play()
                        
                        # 等待当前音频块播放完成
                        while pygame.mixer.get_busy():
                            pygame.time.wait(1)
                            
                    except pygame.error as e:
                        print(f"播放音频块时出错: {e}")
                    finally:
                        audio_buffer.close()
                else:
                    # 队列为空，短暂等待
                    pygame.time.wait(5)
        except Exception as e:
            print(f"音频播放线程错误: {e}")
        finally:
            self.is_playing = False
    
    def stop(self):
        """停止播放"""
        self.is_playing = False
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1)
        pygame.mixer.quit()

class FashionComplimentSystem:
    def __init__(self):
        
        
        # 摄像头配置
        self.picam2 = None
        self.is_detecting = False
        self.last_detection_time = 0
        self.detection_cooldown = 45  # 检测冷却时间(秒)
        
        # 人像检测配置
        self.face_cascade = None
        self.body_cascade = None
        self.detection_lock = Lock()
        
        # 语音播放配置
        pygame.mixer.init()
        self.is_playing = False
        self.audio_player = StreamAudioPlayer(sample_rate=4000)
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化各个组件"""
        try:
            # 初始化摄像头
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"size": (640, 480)},
                controls={"FrameRate": 30},
                transform=Transform(hflip=True, vflip=True)
            )
            self.picam2.configure(config)
            
            
            cascade_path = r'/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml' 
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            logger.info("系统初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def detect_human(self, frame):
        """检测画面中是否有人"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 面部检测
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        
        human_detected = len(faces) > 0 
        
        # 在画面上绘制检测结果
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, 'Face', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
        return human_detected, frame
    
    def capture_image(self):
        """捕获当前画面"""
        try:
            # 使用picamera2捕获图像
            array = self.picam2.capture_array()
            # 转换为BGR格式用于OpenCV处理
            frame = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
            return True, frame
        except Exception as e:
            logger.error(f"捕获图像失败: {e}")
            return False, None
    
    def image_to_base64(self, image):
        """将图像转换为base64编码"""
        try:
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 80])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            return image_base64
        except Exception as e:
            logger.error(f"图像编码失败: {e}")
            return None

    def emotion_recognition(self):
        """使用DeepFace库（基于OpenCV和深度学习）"""
        try:
            # 分析情绪
            result = DeepFace.analyze(
                img_path=self.picam2.capture_array(),
                actions=['emotion'],
                detector_backend='opencv',
                enforce_detection=False,  # 如果未检测到人脸则抛出异常
                align=True  # 对齐人脸以提高准确率
            )
            result1 = result[0]['dominant_emotion']
            return result1  # 返回第一个检测到的人脸结果
        except Exception as e:
            return {"error": str(e)}

    def get_time(self):
        """
        获取当前时间的基本函数
        返回格式化的时间字符串
        """
        # 获取当前日期时间
        now = datetime.now()

        # 格式化为字符串
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")

        return current_time

    def get_location(self):
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
            response = requests.get('https://api.ip.sb/geoip/', headers=headers)
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

    def get_current_weather(self):
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

                response = requests.get(url, timeout=50)
                # print(response.json())
                if response.status_code == 200:
                    return response.json()
            except:
                pass
            return None

        # 3. 主逻辑
        try:
            # 获取当前位置
            location = self.get_location()
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

    def build_prompt(self):
        prompt =f"""请根据这张人物照片，生成一段热情洋溢的穿衣搭配夸奖。重点描述：
    1. 服装的颜色搭配和风格
    2. 整体的时尚感和个人气质
    3. 具体的穿搭亮点
    要求语言生动有趣，充满赞美之情，长度在50-80字左右,并结合以下时间地点天气情绪信息
    天气{self.get_current_weather()}
    地点是{self.get_location()}
    时间是{self.get_time()}
    人物的心情是{self.emotion_recognition()}
"""
        print(prompt)
        return prompt

    def call_doubao_api(self, image_base64):
        """
            调用豆包API生成穿衣夸夸文本
            使用豆包API的实际接口进行调用
        """
        try:
            import requests
            import json
            import random
            
            # 豆包API的端点（请根据实际API文档调整）
            api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"  # 示例URL，需替换为真实端点
            
            # API密钥（建议从环境变量或配置文件中获取）
            api_key = "f011783a-b295-4c4e-a2f6-14a974e74721"  # 需要替换为实际的API密钥

            
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # 构建请求数据
            payload = {
                "model": "doubao-seed-1-6-251015",  # 根据实际模型名称调整
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.build_prompt()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.7
            }
            
            # 发送API请求
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()  # 如果请求失败会抛出异常
            
            # 解析响应
            result = response.json()
            compliment = result["choices"][0]["message"]["content"].strip()
            
            logger.info(f"豆包API生成的夸夸文本: {compliment}")
            return True, compliment
            
        except requests.exceptions.RequestException as e:
            logger.error(f"调用豆包API网络请求失败: {e}")
            # 网络异常时使用备用夸赞语句
            backup_compliments = [
                "哇!你这身搭配真是太有品味了!颜色的搭配非常和谐，整体造型既时尚又显气质，完美展现了你的个人风格!",
                "今天的穿搭真是让人眼前一亮!服装的剪裁和配色都恰到好处，既显瘦又显高，简直是时尚达人的典范!",
                "这套衣服真的太适合你了!简约而不简单，细节处见真章，完美衬托出你的优雅气质和时尚感!",
                "你的穿衣风格总是这么出众!这次的搭配色彩明快，款式新颖，既显年轻活力又不失稳重，真是太棒了!"
            ]
            compliment = random.choice(backup_compliments)
            logger.info(f"使用备用夸夸文本: {compliment}")
            return True, compliment
            
    def call_volcano_tts(self, text):
        """调用火山引擎TTS流式API并实时播放音频"""
        url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
        headers = {
            "X-Api-App-Id": "8107457253",
            "X-Api-Access-Key": "t_ajqQveQiv5B-BaIWao2Ma0G4WKJI_A",
            "X-Api-Resource-Id": "seed-tts-2.0",
            "Content-Type": "application/json",
            "Connection": "keep-alive"
        }
        payload = {
            "req_params":{
                "text": text,
                "speaker": "zh_female_meilinvyou_saturn_bigtts",
                "audio_params": {
                    "format": "mp3",
                    "sample_rate": 4000,
                    "enable_timestamp": True
                },
                "additions": "{\"explicit_language\":\"zh\",\"disable_markdown_filter\":true, \"enable_timestamp\":true}\"}"
            }
        }

        session = requests.Session()
        try:
            print('开始TTS流式请求...')
            response = session.post(url, headers=headers, json=payload, stream=True, timeout=30)
            print(f"响应状态码: {response.status_code}")
            
            logid = response.headers.get('X-Tt-Logid')
            print(f"X-Tt-Logid: {logid}")

            # 实时处理音频流
            for chunk in response.iter_lines(decode_unicode=True):
                if not chunk:
                    continue
                    
                try:
                    data = json.loads(chunk)
                    
                    # 处理音频数据
                    if data.get("code", 0) == 0 and "data" in data and data["data"]:
                        chunk_audio = base64.b64decode(data["data"])
                        print(f"收到音频数据块，大小: {len(chunk_audio)} 字节")
                        self.audio_player.add_audio_chunk(chunk_audio)
                        
                    # 处理文本信息
                    elif data.get("code", 0) == 0 and "sentence" in data and data["sentence"]:
                        print(f"文本信息: {data['sentence']}")
                        
                    # 流结束
                    elif data.get("code", 0) == 20000000:
                        print("TTS流结束")
                        break
                        
                    # 错误处理
                    elif data.get("code", 0) > 0:
                        print(f"TTS错误响应: {data}")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                except Exception as e:
                    print(f"处理数据块时出错: {e}")

        except Exception as e:
            print(f"TTS请求失败: {e}")
        finally:
            response.close()
            session.close()		
    
    def process_detection(self):
        """处理检测到的人像"""
        with self.detection_lock:
            current_time = time.time()
            if current_time - self.last_detection_time < self.detection_cooldown:
                return
            
            # 更新检测时间
            self.last_detection_time = current_time
            
            # 捕获图像
            success, frame = self.capture_image()
            if not success:
                return
            
            # 检测人像
            human_detected, detected_frame = self.detect_human(frame.copy())
            
            if human_detected:
                logger.info("检测到人像，开始处理...")
                
                # 在新线程中处理后续流程
                process_thread = Thread(target=self._process_compliment, args=(frame,))
                process_thread.daemon = True
                process_thread.start()
    
    def _process_compliment(self, image):
        """处理夸夸流程"""
        # 图像编码
        image_base64 = self.image_to_base64(image)
        if image_base64 is None:
            return
            
        # 调用豆包API生成文本
        success, compliment_text = self.call_doubao_api(image_base64)
        if not success:
            return
            
        # 调用TTS转换为语音
        self.is_playing = True
        tts_success = self.call_volcano_tts(compliment_text)
        self.is_playing = False
        

    def start_detection(self):
        """开始人像检测"""
        try:
            self.picam2.start()
            self.is_detecting = True
            
            logger.info("开始人像检测...")
            print("系统已启动，正在检测人像...")
            # print("按 'q' 键退出程序")
            
            while self.is_detecting:
                # 捕获帧进行检测
                success, frame = self.capture_image()
                if success:
                    # 检测人像
                    human_detected, display_frame = self.detect_human(frame)
                    
                    # 显示检测画面（可选）
                    cv2.imshow('Human Detection', display_frame)
                    
                    if human_detected:
                        self.process_detection()
                    
                    # 检测按键输入
                    # key = cv2.waitKey(1) & 0xFF
                    # if key == ord('q'):
                    #     break
                
                # 控制检测频率
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("程序被用户中断")
        except Exception as e:
            logger.error(f"检测过程中出错: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止检测并清理资源"""
        self.is_detecting = False
        if self.picam2:
            self.picam2.stop()
        cv2.destroyAllWindows()
        logger.info("系统已停止")

def main():
    """主函数"""
    print("=" * 50)
    print("树莓派穿衣夸夸系统")
    print("=" * 50)
    
    try:
        # 创建系统实例
        system = FashionComplimentSystem()
        
        # 启动检测
        system.start_detection()
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        print(f"错误: {e}")
        print("请检查摄像头连接和依赖库安装")

if __name__ == "__main__":
    main()
