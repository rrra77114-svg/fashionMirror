from deepface import DeepFace
import cv2


def emotion_recognition_deepface():
    """使用DeepFace库（基于OpenCV和深度学习）"""
    try:
        # 分析情绪
        result = DeepFace.analyze(
            img_path="D03FB490D881DC9F5BEF899EF54A67B9.jpg",
            actions=['emotion'],
            detector_backend='opencv'  # 使用OpenCV进行人脸检测
        )
        print(result)
        return result[0]  # 返回第一个检测到的人脸结果
    except Exception as e:
        return {"error": str(e)}


# 使用示例
result = emotion_recognition_deepface()
print("主导情绪:", result['dominant_emotion'])
print("所有情绪:", result['emotion'])