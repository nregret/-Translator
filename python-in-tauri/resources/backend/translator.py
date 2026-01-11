import asyncio
import logging
from typing import Dict, Optional
import importlib.util

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Translator:
    def __init__(self):
        self.llm_instance = None
        self.inference_mode = "cpu"  # 默认CPU模式
        self._need_recreate = False  # 标记是否需要重新创建实例
    
    async def init(self):
        """初始化翻译器"""
        logger.info("翻译器初始化完成")
    
    async def cleanup(self):
        """清理翻译器资源"""
        if self.llm_instance:
            try:
                del self.llm_instance
            except:
                pass
            self.llm_instance = None
        logger.info("翻译器资源清理完成")
    
    async def translate(self, text: str, source_lang: str = "auto", target_lang: str = "zh", provider: str = "llama-cpp") -> Dict[str, str]:
        """
        统一的翻译接口
        """
        if provider == "llama-cpp":
            return await self.translate_with_llama_cpp(text, source_lang, target_lang)
        elif provider == "baidu":
            return await self.translate_with_baidu(text, source_lang, target_lang)
        else:
            return {
                "success": False,
                "error": f"不支持的翻译提供商: {provider}"
            }
    
    async def translate_with_llama_cpp(self, text: str, source_lang: str = "auto", target_lang: str = "zh") -> Dict[str, str]:
        """
        使用llama-cpp-python加载GGUF模型进行翻译 (仅CPU模式)
        """
        try:
            # 动态导入，避免在没有安装时出错
            from llama_cpp import Llama
            import json
            import os
            
            # 从配置文件加载参数
            config_path = "../config.json"
            config_file_path = os.path.join(os.path.dirname(__file__), config_path)
            config = {}
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 使用配置文件中的参数，如果没有则使用默认值
            model_dir = config.get("model_dir", "./models")
            current_model = config.get("current_model", "")
            context_length = config.get("context_length", 2048)
            threads = config.get("threads", 4)
            max_tokens = config.get("max_tokens", 512)
            temperature = config.get("temperature", 0.1)
            
            # 构建模型路径
            if not os.path.isabs(model_dir):
                base_dir = os.path.dirname(__file__)
                model_dir = os.path.join(base_dir, "..", model_dir)
                model_dir = os.path.normpath(model_dir)
            
            # 如果没有指定当前模型，尝试查找第一个 .gguf 文件
            if not current_model:
                if os.path.exists(model_dir):
                    for file in os.listdir(model_dir):
                        if file.endswith('.gguf'):
                            current_model = file
                            break
            
            if not current_model:
                return {
                    "success": False,
                    "error": f"模型文件夹中没有找到 .gguf 文件: {model_dir}"
                }
            
            model_path = os.path.join(model_dir, current_model)
            
            # 注意：用户需要先下载合适的GGUF翻译模型文件
            # 这里提供一个通用的翻译提示模板
            # 实际使用时需要一个专门的翻译模型，如Qwen、Mistral等微调模型
            
            # 构建翻译提示（使用混元模型的提示词模板）
            # 根据目标语言构建提示词
            target_lang_map = {
                "zh": "中文",
                "en": "English",
                "ja": "日本語",
                "ko": "한국어",
                "fr": "Français",
                "de": "Deutsch",
                "es": "Español",
                "ru": "Русский",
                "ar": "العربية",
                "it": "Italiano",
                "pt": "Português",
                "nl": "Nederlands",
                "pl": "Polski",
                "vi": "Tiếng Việt",
                "th": "ไทย",
                "tr": "Türkçe",
                "he": "עברית",
                "hi": "हिन्दी",
                "cs": "Čeština",
                "uk": "Українська",
                "id": "Bahasa Indonesia",
                "ms": "Bahasa Melayu",
                "tl": "Filipino",
                "bn": "বাংলা",
                "ta": "தமிழ்",
                "te": "తెలుగు",
                "mr": "मराठी",
                "gu": "ગુજરાતી",
                "kn": "ಕನ್ನಡ",
                "ml": "മലയാളം",
                "si": "සිංහල",
                "my": "မြန်မာဘာသာ",
                "km": "ភាសាខ្មែរ",
                "lo": "ລາວ",
                "fa": "فارسی",
                "ur": "اردو",
                "pa": "ਪੰਜਾਬੀ",
                "kk": "Қазақ тілі",
                "uz": "O'zbek tili",
                "mn": "Монгол хэл",
                "bo": "བོད་སྐད།",
                "ug": "ئۇيغۇر تىلى",
                "yue": "粵語",
                "zh-Hant": "繁體中文"
            }
            
            target_display = target_lang_map.get(target_lang, target_lang)
            prompt = f"将以下文本翻译为{target_display}，注意只需要输出翻译后的结果，不要额外解释：\n\n{text}"
            
            # 检查模型文件是否存在
            if not os.path.exists(model_path):
                # 如果没有找到翻译专用模型，提示用户下载或使用通用模型
                logger.warning(f"翻译模型未找到: {model_path}，请下载合适的GGUF格式翻译模型")
                return {
                    "success": False,
                    "error": f"模型文件不存在: {model_path}。请下载合适的GGUF格式翻译模型"
                }
            
            # 如果模型实例不存在或推理模式已更改，则创建新实例
            if self.llm_instance is None or hasattr(self, '_need_recreate') and self._need_recreate:
                # CPU推理参数设置 (仅Windows)
                # 如果已有实例，先清理旧实例
                if self.llm_instance is not None:
                    logger.info("清理旧模型实例")
                    try:
                        # 尝试清理当前实例
                        del self.llm_instance
                    except:
                        pass
                    self.llm_instance = None
                
                # 创建模型实例
                logger.info(f"创建CPU模型实例，模型路径: {model_path}，线程数: {threads}")
                self.llm_instance = Llama(**{
                    "model_path": model_path,
                    "n_ctx": context_length,  # 从配置文件获取上下文长度
                    "n_gpu_layers": 0,  # 禁用GPU，仅使用CPU
                    "n_threads": threads,  # 从配置文件获取线程数
                    "verbose": False  # 关闭详细输出
                })
                if hasattr(self, '_need_recreate'):
                    delattr(self, '_need_recreate')
            
            # 使用现有模型实例执行翻译（使用流式输出）
            logger.info(f"开始CPU翻译")
            translated_text = ""
            
            # 使用流式生成
            output = self.llm_instance(
                prompt,
                max_tokens=max_tokens,  # 从配置文件获取最大token数
                temperature=temperature,  # 从配置文件获取温度
                stop=["\n\n", "###"],  # 停止词
                stream=True  # 启用流式输出
            )
            
            # 收集流式输出
            for chunk in output:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('text', '')
                    if delta:
                        translated_text += delta
            
            return {
                "success": True,
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
        except ImportError:
            logger.error("llama-cpp-python库未安装，请运行: pip install llama-cpp-python")
            return {
                "success": False,
                "error": "llama-cpp-python库未安装，请运行: pip install llama-cpp-python"
            }
        except Exception as e:
            logger.error(f"llama-cpp翻译出错: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def translate_with_baidu(self, text: str, source_lang: str = "auto", target_lang: str = "zh") -> Dict[str, str]:
        """
        使用百度翻译API进行翻译
        """
        try:
            import requests
            import random
            from hashlib import md5
            import json
            import os
            
            # 从配置文件加载参数
            config_path = os.path.join(os.path.dirname(__file__), "../config.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            appid = config.get("baidu_appid", "")
            appkey = config.get("baidu_appkey", "")
            
            if not appid or not appkey:
                return {
                    "success": False,
                    "error": "百度翻译API配置不完整，请在设置中配置App ID和App Key"
                }
            
            # 百度翻译API语言代码映射
            lang_map = {
                "zh": "zh",
                "en": "en",
                "ja": "jp",
                "ko": "kor",
                "fr": "fra",
                "de": "de",
                "es": "spa",
                "ru": "ru",
                "ar": "ara"
            }
            
            # 转换目标语言代码
            to_lang = lang_map.get(target_lang, "zh")
            
            # 处理源语言
            if source_lang == "auto":
                from_lang = "auto"
            else:
                from_lang = lang_map.get(source_lang, "auto")
            
            # 百度翻译API端点
            endpoint = 'http://api.fanyi.baidu.com'
            path = '/api/trans/vip/translate'
            url = endpoint + path
            
            # 生成salt和sign
            def make_md5(s, encoding='utf-8'):
                return md5(s.encode(encoding)).hexdigest()
            
            salt = random.randint(32768, 65536)
            sign = make_md5(appid + text + str(salt) + appkey)
            
            # 构建请求
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = {
                'appid': appid,
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'salt': salt,
                'sign': sign
            }
            
            # 发送请求
            response = requests.post(url, params=payload, headers=headers, timeout=10)
            result = response.json()
            
            # 检查错误
            if 'error_code' in result:
                error_msg = result.get('error_msg', f"错误代码: {result.get('error_code')}")
                logger.error(f"百度翻译API错误: {error_msg}")
                return {
                    "success": False,
                    "error": f"百度翻译API错误: {error_msg}"
                }
            
            # 提取翻译结果
            if 'trans_result' in result and len(result['trans_result']) > 0:
                translated_text = result['trans_result'][0].get('dst', '')
                detected_lang = result.get('from', source_lang)
                
                return {
                    "success": True,
                    "translated_text": translated_text,
                    "source_lang": detected_lang,
                    "target_lang": target_lang
                }
            else:
                return {
                    "success": False,
                    "error": "百度翻译API返回结果格式错误"
                }
                
        except ImportError:
            logger.error("requests库未安装，请运行: pip install requests")
            return {
                "success": False,
                "error": "requests库未安装，请运行: pip install requests"
            }
        except Exception as e:
            logger.error(f"百度翻译出错: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def set_inference_mode(self, mode: str):
        """
        设置推理模式 (仅CPU)
        """
        if mode in ["cpu"]:
            if self.inference_mode != mode:
                self.inference_mode = mode
                # 重置LLM实例以应用新模式
                self.llm_instance = None
                # 标记需要重新创建实例
                self._need_recreate = True
                logger.info(f"推理模式已设置为: {mode}")
            else:
                logger.info(f"推理模式已经是: {mode}")
            return True
        else:
            logger.error(f"无效的推理模式: {mode}，仅支持cpu模式")
            return False
    
    def get_inference_mode(self):
        """
        获取当前推理模式
        """
        return self.inference_mode
    
    def get_gpu_utilization(self):
        """
        获取GPU利用率信息（不适用，仅CPU模式）
        """
        return {
            "gpu_layers_used": 0,
            "is_using_gpu": False,
            "using_cpu": True
        }

    def get_config(self):
        """
        获取配置信息
        优先级：resources/config.json > 用户配置目录 > 默认配置
        """
        import json
        import os
        from pathlib import Path
        
        # 优先查找 resources/config.json（打包后的位置或开发模式的位置）
        # backend 目录在 resources/backend/，所以 ../config.json 就是 resources/config.json
        resources_config_path = os.path.join(os.path.dirname(__file__), "../config.json")
        if os.path.exists(resources_config_path):
            try:
                with open(resources_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 兼容旧的配置格式：如果有 model_path，转换为 model_dir 和 current_model
                    if "model_path" in config and "model_dir" not in config:
                        old_model_path = config["model_path"]
                        # 提取目录和文件名
                        model_dir = os.path.dirname(old_model_path)
                        model_name = os.path.basename(old_model_path)
                        # 如果是相对路径，转换为相对于 resources 的路径
                        if not os.path.isabs(model_dir):
                            base_dir = os.path.dirname(__file__)
                            model_dir = os.path.join(base_dir, "..", model_dir)
                            model_dir = os.path.normpath(model_dir)
                        config["model_dir"] = model_dir
                        config["current_model"] = model_name
                        # 删除旧的 model_path
                        del config["model_path"]
                        # 保存更新后的配置
                        self.update_config(config)
                    return config
            except Exception as e:
                logger.warning(f"读取 resources/config.json 失败: {str(e)}")
        
        # 如果 resources/config.json 不存在，尝试使用用户配置目录（如果 appdirs 可用）
        try:
            import appdirs
            data_dir = appdirs.user_data_dir("TranslatorApp", "Translator")
            user_config_path = Path(data_dir) / "config.json"
            
            if user_config_path.exists():
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except ImportError:
            # appdirs 不可用，跳过用户配置目录
            pass
        except Exception as e:
            logger.warning(f"读取用户配置失败: {str(e)}")
        
        # 如果都没有找到，返回默认配置
        return {
            "model_dir": "./models",
            "current_model": "",
            "context_length": 2048,
            "threads": 4,
            "max_tokens": 512,
            "temperature": 0.1,
            "api_base_url": "http://127.0.0.1:8000",
            "timeout": 5000,
            "auto_copy": False,
            "dark_mode": False,
            "theme_color": "#6366f1"
        }

    def update_config(self, new_config):
        """
        更新配置信息
        优先保存到 resources/config.json（打包后的位置或开发模式的位置）
        """
        import json
        import os
        from pathlib import Path
        
        # 优先保存到 resources/config.json（与读取保持一致）
        config_path = os.path.join(os.path.dirname(__file__), "../config.json")
        try:
            # 确保目录存在
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2, ensure_ascii=False)
            return {"success": True, "message": "配置已保存到 resources/config.json"}
        except Exception as e:
            logger.error(f"保存配置到 resources/config.json 失败: {str(e)}")
            # 如果保存失败，尝试保存到用户配置目录
            try:
                import appdirs
                data_dir = appdirs.user_data_dir("TranslatorApp", "Translator")
                user_config_path = Path(data_dir) / "config.json"
                user_config_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(user_config_path, 'w', encoding='utf-8') as f:
                    json.dump(new_config, f, indent=2, ensure_ascii=False)
                return {"success": True, "message": "配置已保存到用户配置目录"}
            except ImportError:
                # appdirs 不可用
                pass
            except Exception as e2:
                logger.error(f"保存配置到用户目录也失败: {str(e2)}")
            
            return {"success": False, "error": str(e)}
    
    def get_models_list(self):
        """
        获取模型文件夹中的模型列表
        返回所有 .gguf 文件
        """
        import os
        from pathlib import Path
        
        try:
            config = self.get_config()
            model_dir = config.get("model_dir", "./models")
            
            # 如果路径是相对路径，转换为绝对路径
            if not os.path.isabs(model_dir):
                # 相对于 backend 目录
                base_dir = os.path.dirname(__file__)
                model_dir = os.path.join(base_dir, "..", model_dir)
                model_dir = os.path.normpath(model_dir)
            
            if not os.path.exists(model_dir):
                return {
                    "success": False,
                    "error": f"模型文件夹不存在: {model_dir}",
                    "models": []
                }
            
            # 查找所有 .gguf 文件
            models = []
            for file in os.listdir(model_dir):
                if file.endswith('.gguf'):
                    file_path = os.path.join(model_dir, file)
                    file_size = os.path.getsize(file_path)
                    models.append({
                        "name": file,
                        "path": file_path,
                        "size": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
            
            # 按文件名排序
            models.sort(key=lambda x: x["name"])
            
            return {
                "success": True,
                "models": models,
                "model_dir": model_dir
            }
        except Exception as e:
            logger.error(f"获取模型列表失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "models": []
            }
    
    def switch_model(self, model_name):
        """
        切换模型
        如果模型已加载，需要重新加载
        """
        import os
        
        try:
            config = self.get_config()
            model_dir = config.get("model_dir", "./models")
            
            # 如果路径是相对路径，转换为绝对路径
            if not os.path.isabs(model_dir):
                base_dir = os.path.dirname(__file__)
                model_dir = os.path.join(base_dir, "..", model_dir)
                model_dir = os.path.normpath(model_dir)
            
            model_path = os.path.join(model_dir, model_name)
            
            if not os.path.exists(model_path):
                return {
                    "success": False,
                    "error": f"模型文件不存在: {model_path}"
                }
            
            # 更新配置中的当前模型
            config["current_model"] = model_name
            self.update_config(config)
            
            # 标记需要重新创建模型实例
            if self.llm_instance is not None:
                try:
                    del self.llm_instance
                except:
                    pass
                self.llm_instance = None
                self._need_recreate = True
            
            logger.info(f"已切换到模型: {model_name}")
            
            return {
                "success": True,
                "message": f"已切换到模型: {model_name}",
                "model_path": model_path
            }
        except Exception as e:
            logger.error(f"切换模型失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# 全局翻译器实例
translator = Translator()

async def init_translator():
    """初始化翻译器"""
    await translator.init()

async def cleanup_translator():
    """清理翻译器"""
    await translator.cleanup()