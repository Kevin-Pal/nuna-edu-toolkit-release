Nuna音频接收服务器搭建说明

一、基本说明：
APP客户端通过multipart/form-data 的方式向服务器发送两个部分：
file：音频文件本身（MIME 类型为 audio/*）。
metadata：一个 JSON 字符串，封装了以下字段：
userID(用户UserID)
name（文件名）
startTime（开始时间戳）
endTime（结束时间戳）
mac（设备 MAC 地址）
size（文件大小，单位字节）
接口路径为：
POST /thingx/api/file/upload/audio

Android代码段如下：
 

二、服务器搭建示例
可使用Python+FastAPI来接收音频和相关信息数据。

1、安装依赖
pip install "fastapi>=0.100.0" "uvicorn[standard]>=0.24.0" python-multipart

2、参考创建服务代码 snippets/receive_from_nuna_app.py
 

三、新版APP

https://www.pgyer.com/nuna-android-cas

Android V1.9.1更新内容：
1、Me页面添加可配置音频服务器地址入口菜单
2、测试环境/中文模型/音频全量上报