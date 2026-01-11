"""
本地模型推理测试文件
直接调用llama-cpp-python进行翻译测试
"""
import os
from llama_cpp import Llama

def translate_with_local_model(text, source_lang="auto", target_lang="zh"):
    """
    使用本地GGUF模型进行翻译
    """
    try:
        # 模型路径 - 请根据实际情况修改
        model_path = "E:\\Project\\VsCode\\Translater\\SimpleTauri\\python-in-tauri\\resources\\models\\HY-MT1.5-1.8B-Q4_K_M.gguf"
        
        # 检查模型文件是否存在
        if not os.path.exists(model_path):
            print(f"错误: 模型文件不存在: {model_path}")
            print("请先下载GGUF格式的翻译模型，例如:")
            print("- NLLB多语言模型")
            print("- M2M100多语言模型")
            print("- Qwen系列多语言模型")
            return None
        
        # 构建翻译提示
        if source_lang == "auto" or source_lang == "en":
            if target_lang == "zh":
                prompt = f"请将以下英文文本翻译成中文: {text}"
            elif target_lang == "fr":
                prompt = f"Please translate the following English text to French: {text}"
            elif target_lang == "de":
                prompt = f"Please translate the following English text to German: {text}"
            elif target_lang == "es":
                prompt = f"Please translate the following English text to Spanish: {text}"
            else:
                prompt = f"Please translate the following English text to {target_lang}: {text}"
        else:
            prompt = f"Translate the following text from {source_lang} to {target_lang}: {text}"
        
        # 加载模型
        print("正在加载模型...")
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,  # 上下文长度
            n_threads=4,  # 使用的线程数
            verbose=False  # 关闭详细输出
        )
        
        print("正在执行翻译...")
        # 执行翻译
        output = llm(
            prompt,
            max_tokens=512,  # 最大输出token数
            temperature=0.1,  # 低温度以获得更确定性的输出
            stop=["\n\n", "###"]  # 停止词
        )
        
        translated_text = output['choices'][0]['text'].strip()
        return translated_text
        
    except Exception as e:
        print(f"翻译出错: {str(e)}")
        return None

def main():
    """
    主函数 - 测试本地模型翻译
    """
    print("本地模型翻译测试")
    print("="*50)
    
    # 测试用例
    test_cases = [
        ("Hello, how are you today?", "en", "zh"),
        ("Good morning everyone!", "en", "zh"),
        ("今天天气真好。", "zh", "en"),
        ("Welcome to the beautiful city.", "en", "zh"),
    ]
    
    for text, source_lang, target_lang in test_cases:
        print(f"\n原文: {text}")
        print(f"源语言: {source_lang}, 目标语言: {target_lang}")
        
        result = translate_with_local_model(text, source_lang, target_lang)
        
        if result:
            print(f"译文: {result}")
        else:
            print("翻译失败")
        
        print("-" * 30)
    
    # 交互式测试
    print("\n交互式测试 (输入 'quit' 退出):")
    while True:
        user_input = input("\n请输入要翻译的文本: ").strip()
        if user_input.lower() == 'quit':
            break
        
        if user_input:
            target_lang = input("请输入目标语言 (如: zh, en, fr, de, es) [默认: zh]: ").strip()
            if not target_lang:
                target_lang = "zh"
                
            result = translate_with_local_model(user_input, "auto", target_lang)
            
            if result:
                print(f"译文: {result}")
            else:
                print("翻译失败")

if __name__ == "__main__":
    main()