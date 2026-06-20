import os
import dashscope

# 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1，若使用美国地域的模型，需将url替换为：https://dashscope-us.aliyuncs.com/api/v1
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

# 请用您的本地音频的绝对路径替换 ABSOLUTE_PATH/welcome.mp3
# audio_file_path = "file://ABSOLUTE_PATH/welcome.mp3"
audio_file_path = "file:///path/to/nuna-edu-toolkit/runtime/data/audio/<user_id>/<date>/<segment>.wav"

messages = [
    {"role": "user", "content": [{"audio": audio_file_path}]},   # content为用户消息的内容，仅允许设置一组消息 （NOTE：一会可以试试能不能messages里放多条消息然后并发识别）——完全不允许多条消息，只能多次调用
]
response = dashscope.MultiModalConversation.call(
    # 新加坡/美国地域和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key = "sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 若使用美国地域的模型，需在模型后面加上“-us”后缀，例如qwen3-asr-flash-us
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
    asr_options={
        # "language": "zh", # 可选，若已知音频的语种，可通过该参数指定待识别语种，以提升识别准确率
        "enable_itn":False  # 可选，是否开启反规范化，默认为True，开启后会将数字、日期等内容进行反规范化处理，例如“2024年6月”会被识别为“2024年6月”，关闭后则会被识别为“二零二四年六月”
    }
)
print(response)

