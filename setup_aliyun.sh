#!/bin/bash
echo "开始安装依赖..."

# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装系统依赖
sudo apt install -y python3-pip python3-venv libatlas-base-dev libjasper-dev libqtgui4 libqt4-test libhdf5-dev libhdf5-serial-dev libopenblas-dev

# 创建虚拟环境
python3 -m venv mirror_env
source mirror_env/bin/activate

# 安装Python包
pip install --upgrade pip
pip install numpy==1.24.3 -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com
pip install opencv-python-headless==4.8.1.78 -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com
pip install requests pygame deepface picamera2 pillow -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com

echo "安装完成！"
echo "激活虚拟环境: source mirror_env/bin/activate"