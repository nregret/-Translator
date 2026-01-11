"""
模型下载脚本
用于下载GGUF格式的翻译模型
"""
import os
import requests
from pathlib import Path

def download_file(url, filename, chunk_size=8192):
    """
    下载文件的辅助函数
    """
    print(f"正在下载 {filename}...")
    
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded_size / total_size) * 100
                        print(f"\r进度: {percent:.1f}% ({downloaded_size}/{total_size} bytes)", end='', flush=True)
        
        print(f"\n下载完成: {filename}")

def download_translation_model(model_url, model_filename):
    """
    下载翻译模型
    """
    models_dir = Path("./models")
    models_dir.mkdir(exist_ok=True)
    
    model_path = models_dir / model_filename
    
    if model_path.exists():
        print(f"模型已存在: {model_path}")
        return str(model_path)
    
    try:
        download_file(model_url, str(model_path))
        print(f"模型下载成功: {model_path}")
        return str(model_path)
    except Exception as e:
        print(f"下载失败: {e}")
        return None

def main():
    """
    主函数 - 提供几个常见的多语言模型选项
    """
    print("可用的GGUF翻译模型:")
    print("1. nllb-dedup-2.7B (多语言翻译模型)")
    print("2. m2m100_418M (多语言翻译模型)")
    print("3. Qwen2-7B-Instruct (多语言大模型，可做翻译)")
    print("4. 自定义模型URL")
    
    choice = input("\n请选择模型类型 (1-4): ").strip()
    
    model_info = {
        "1": {
            "name": "nllb-dedup-2.7B",
            "url": "https://huggingface.co/TheBloke/NLLB-200-Distilled-600M-GGUF/resolve/main/nllb-200-distilled-600m.Q4_K_M.gguf",  # 示例URL
            "filename": "nllb_distilled_600m.Q4_K_M.gguf"
        },
        "2": {
            "name": "m2m100_418M",
            "url": "https://huggingface.co/TheBloke/m2m100_418M-GGML/resolve/main/m2m100_418m.bin",  # 示例URL
            "filename": "m2m100_418m.gguf"
        },
        "3": {
            "name": "Qwen2-7B-Instruct",
            "url": "https://huggingface.co/Qwen/Qwen2-7B-Instruct-GGUF/resolve/main/qwen2-7b-instruct.q4_k_m.gguf",  # 示例URL
            "filename": "qwen2_7b_instruct.q4_k_m.gguf"
        }
    }
    
    if choice in model_info:
        info = model_info[choice]
        print(f"\n即将下载 {info['name']} 模型...")
        print(f"URL: {info['url']}")
        print(f"保存为: ./models/{info['filename']}")
        
        confirm = input("\n确认下载? (y/N): ").lower()
        if confirm == 'y':
            model_path = download_translation_model(info['url'], info['filename'])
            if model_path:
                print(f"\n模型已下载到: {model_path}")
                print("\n要使用此模型，请在translator.py中将model_path改为:")
                print(f'model_path = "{model_path}"')
            else:
                print("下载失败")
        else:
            print("取消下载")
    elif choice == "4":
        custom_url = input("请输入模型的下载URL: ").strip()
        if custom_url:
            custom_filename = input("请输入保存的文件名 (如 model.gguf): ").strip()
            if custom_filename:
                model_path = download_translation_model(custom_url, custom_filename)
                if model_path:
                    print(f"\n模型已下载到: {model_path}")
                    print("\n要使用此模型，请在translator.py中将model_path改为:")
                    print(f'model_path = "{model_path}"')
                else:
                    print("下载失败")
            else:
                print("无效的文件名")
        else:
            print("无效的URL")
    else:
        print("无效的选择")

if __name__ == "__main__":
    main()