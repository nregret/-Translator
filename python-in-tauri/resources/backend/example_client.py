"""
翻译API客户端示例
展示如何从前端或外部程序调用翻译服务
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def translate_text(text, source_lang="auto", target_lang="zh", provider="llama-cpp"): 
    """
    调用翻译API
    """
    url = f"{BASE_URL}/translate"
    
    payload = {
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "provider": provider
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 抛出异常如果状态码不是2xx
        
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
    except json.JSONDecodeError:
        print("响应不是有效的JSON格式")
        return None

def batch_translate_texts(texts, source_lang="auto", target_lang="zh", provider="llama-cpp"): 
    """
    批量翻译文本
    """
    url = f"{BASE_URL}/batch_translate"
    
    params = {
        "source_lang": source_lang,
        "target_lang": target_lang,
        "provider": provider
    }
    
    try:
        response = requests.post(url, json=texts, params=params)
        response.raise_for_status()
        
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        print(f"批量请求失败: {e}")
        return None

def check_health():
    """
    检查API健康状态
    """
    url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        print(f"健康检查失败: {e}")
        return None

if __name__ == "__main__":
    # 测试健康检查
    print("=== 健康检查 ===")
    health = check_health()
    if health:
        print(f"服务状态: {health}")
    else:
        print("无法连接到服务，请确保翻译API正在运行")
        exit(1)
    
    # 测试单个翻译
    print("\n=== 单个翻译测试 ===")
    test_text = "Hello, how are you today?"
    result = translate_text(test_text, target_lang="zh")
    
    if result and result["success"]:
        print(f"原文: {result['original_text']}")
        print(f"译文: {result['translated_text']}")
        print(f"源语言: {result['source_lang']}, 目标语言: {result['target_lang']}")
    else:
        print("翻译失败")
    
    # 测试批量翻译
    print("\n=== 批量翻译测试 ===")
    test_texts = [
        "Hello, world!",
        "How are you?",
        "Thank you very much."
    ]
    
    batch_result = batch_translate_texts(test_texts, target_lang="zh")
    
    if batch_result and batch_result["success"]:
        for i, item in enumerate(batch_result["results"]):
            print(f"文本 {i+1}:")
            print(f"  原文: {item['original_text']}")
            print(f"  译文: {item['translated_text']}")
            print(f"  成功: {item['success']}")
            if not item['success']:
                print(f"  错误: {item['error']}")
    else:
        print("批量翻译失败")