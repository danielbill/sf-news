Rate limit reached for TPM错误表示您已经达到了百度千帆大模型的每分钟请求限制（TPM，即Tokens Per Minute）。每个API调用都有一个TPM限制，超出限制后，请求会被拒绝，直到下一分钟重新计算。

解决方法：
降低请求频率：减少每分钟的请求次数，确保不超过TPM限制。可以在代码中加入延迟或批量处理请求。

检查TPM配额：登录百度智能云控制台，查看您的TPM配额。如果需要更高的配额，可以联系百度客服申请升级。

优化请求内容：减少每次请求的token数量，例如缩短输入文本或减少生成文本的长度。

使用异步处理：将请求分散到不同的时间段，避免集中请求。

代码示例（Python）：
import time
import requests

def call_api_with_retry(prompt, max_retries=3):
    url = "https://your-baidu-api-endpoint"
    headers = {
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "max_tokens": 100
    }

    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 429:  # 429表示限速错误
            print(f"Rate limit reached, retrying in 60 seconds... (Attempt {attempt + 1})")
            time.sleep(60)  # 等待60秒后重试
        else:
            return response.json()
    raise Exception("Max retries reached, still receiving rate limit error.")

# 调用示例
response = call_api_with_retry("你好，请生成一段文本。")
print(response)
总结：
通过调整请求频率、优化请求内容或申请更高的配额，可以有效避免Rate limit reached for TPM错误。