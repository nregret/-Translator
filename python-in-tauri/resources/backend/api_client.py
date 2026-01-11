"""
API客户端调用文件
用于调用FastAPI翻译服务
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

def main():
    """
    主函数 - 测试API调用
    """
    print("API客户端测试")
    print("="*50)
    
    # 首先检查服务是否运行
    print("检查服务状态...")
    health = check_health()
    if health:
        print(f"服务状态: {health}")
    else:
        print("无法连接到服务，请确保翻译API正在运行")
        print("运行方法: python translation_api.py")
        return
    
    # 测试单个翻译
    print("\n=== 单个翻译测试 ===")
    test_text = "Hello, how are you today?"
    result = translate_text(test_text, target_lang="zh", provider="llama-cpp")
    
    if result and result["success"]:
        print(f"原文: {result['original_text']}")
        print(f"译文: {result['translated_text']}")
        print(f"源语言: {result['source_lang']}, 目标语言: {result['target_lang']}")
    else:
        print("翻译失败")
        if result:
            print(f"错误信息: {result.get('error', '未知错误')}")
    
    # 测试批量翻译
    print("\n=== 批量翻译测试 ===")
    test_texts = [
        "Hello, world!",
        "How are you?",
        "Thank you very much.",
        "Have a nice day!"
    ]
    
    batch_result = batch_translate_texts(test_texts, target_lang="zh", provider="llama-cpp")
    
    if batch_result and batch_result["success"]:
        for i, item in enumerate(batch_result["results"]):
            print(f"文本 {i+1}:")
            print(f"  原文: {item['original_text']}")
            print(f"  译文: {item['translated_text']}")
            print(f"  成功: {item['success']}")
            if not item['success']:
                print(f"  错误: {item['error']}")
            print()
    else:
        print("批量翻译失败")
        if batch_result:
            print(f"错误信息: {batch_result.get('error', '未知错误')}")
    
    # 交互式测试
    print("\n=== 交互式API测试 ===")
    print("输入文本进行翻译 (输入 'quit' 退出):")
    
    while True:
        user_input = input("\n请输入要翻译的文本: ").strip()
        if user_input.lower() == 'quit':
            break
        
        if user_input:
            target_lang = input("请输入目标语言 (如: zh, en, fr, de, es) [默认: zh]: ").strip()
            if not target_lang:
                target_lang = "zh"
            
            provider = input("请输入翻译提供商 (llama-cpp, openai) [默认: llama-cpp]: ").strip()
            if not provider:
                provider = "llama-cpp"
            
            result = translate_text(user_input, target_lang=target_lang, provider=provider)
            
            if result and result["success"]:
                print(f"译文: {result['translated_text']}")
            else:
                print("翻译失败")
                if result:
                    print(f"错误信息: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    main()