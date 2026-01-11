from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import asyncio
from typing import Dict, Optional

# 添加当前目录到模块搜索路径
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translator import translator, init_translator, cleanup_translator

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="Translation API", version="1.0.0")

# 添加CORS中间件以支持前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应指定具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求数据模型
class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh"
    provider: str = "llama-cpp"


class InferenceModeRequest(BaseModel):
    mode: str


class BatchFileTranslationRequest(BaseModel):
    file_paths: list[str]
    target_lang: str = "zh"
    source_lang: str = "auto"
    provider: str = "llama-cpp"
    save_mode: str = "replace"  # "replace" or "save_as"
    save_path: Optional[str] = None  # 仅当save_mode为"save_as"时使用


class BatchFileTranslationRequest(BaseModel):
    file_paths: list[str]
    target_lang: str = "zh"
    source_lang: str = "auto"
    provider: str = "llama-cpp"
    save_mode: str = "replace"  # "replace" or "save_as"
    save_path: Optional[str] = None  # 仅当save_mode为"save_as"时使用


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化翻译器"""
    logger.info("正在初始化翻译器...")
    await init_translator()
    logger.info("翻译器初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("正在清理翻译器资源...")
    await cleanup_translator()
    logger.info("翻译器资源清理完成")


@app.post("/translate")
async def translate(request: TranslationRequest):
    """
    执行翻译操作
    """
    try:
        logger.info(f"收到翻译请求: {request.text[:50]}...")
        
        result = await translator.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider=request.provider
        )
        
        if result["success"]:
            logger.info("翻译成功")
            return {
                "success": True,
                "original_text": request.text,
                "translated_text": result["translated_text"],
                "source_lang": result.get("source_lang", request.source_lang),
                "target_lang": result.get("target_lang", request.target_lang)
            }
        else:
            logger.error(f"翻译失败: {result.get('error', '未知错误')}")
            raise HTTPException(status_code=400, detail=result.get("error", "翻译失败"))
            
    except Exception as e:
        logger.error(f"翻译过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate-stream")
async def translate_stream(request: TranslationRequest):
    """
    执行流式翻译操作，实时返回生成的文本
    """
    async def event_generator():
        try:
            logger.info(f"收到流式翻译请求: {request.text[:50]}...")
            
            # 动态导入llama-cpp-python
            from llama_cpp import Llama
            import json
            
            # 从配置文件加载参数
            # 尝试使用appdirs，如果不可用则回退
            try:
                import appdirs
                import pathlib
                config_dir = pathlib.Path(appdirs.user_data_dir("TranslatorApp", "Translator"))
                config_file_path = config_dir / "config.json"
                config_path = str(config_file_path)
            except ImportError:
                # 如果appdirs不可用，回退到原始方法
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
                yield f"data: {json.dumps({'error': f'模型文件夹中没有找到 .gguf 文件: {model_dir}'})}\n\n"
                return
            
            model_path = os.path.join(model_dir, current_model)
            
            # 构建翻译提示（使用混元模型的提示词模板）
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
            
            target_display = target_lang_map.get(request.target_lang, request.target_lang)
            prompt = f"将以下文本翻译为{target_display}，注意只需要输出翻译后的结果，不要额外解释：\n\n{request.text}"
            
            # 检查模型文件是否存在
            if not os.path.exists(model_path):
                yield f"data: {json.dumps({'error': f'模型文件不存在: {model_path}'})}\n\n"
                return
            
            # 如果模型实例不存在，则创建新实例
            if translator.llm_instance is None:
                translator.llm_instance = Llama(
                    model_path=model_path,
                    n_ctx=context_length,
                    n_gpu_layers=0,  # 禁用GPU，仅使用CPU
                    n_threads=threads,
                    verbose=False
                )
            
            # 使用流式生成
            output = translator.llm_instance(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n", "###"],
                stream=True
            )
            
            # 逐个yield生成的文本，添加flush确保实时发送
            for chunk in output:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('text', '')
                    if delta:
                        yield f"data: {json.dumps({'text': delta})}\n\n"
                        # 强制刷新，确保数据立即发送
                        # 在FastAPI中，我们通过yield来实时发送数据
                        
            # 发送结束信号
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"流式翻译过程中发生错误: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # 使用正确的响应头以确保流式传输
    return StreamingResponse(
        event_generator(), 
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy", "service": "translation-api"}


@app.post("/batch_translate")
async def batch_translate(
    texts: list[str],
    source_lang: str = Query(default="auto", description="源语言"),
    target_lang: str = Query(default="zh", description="目标语言"),
    provider: str = Query(default="openai", description="翻译服务提供商")
):
    """
    批量翻译接口
    """
    try:
        logger.info(f"收到批量翻译请求，共{len(texts)}个文本")
        
        results = []
        for text in texts:
            result = await translator.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=provider
            )
            
            results.append({
                "original_text": text,
                "translated_text": result.get("translated_text", ""),
                "success": result["success"],
                "error": result.get("error", "") if not result["success"] else None
            })
        
        return {
            "success": True,
            "results": results,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        
    except Exception as e:
        logger.error(f"批量翻译过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-inference-mode")
async def update_inference_mode(request: InferenceModeRequest):
    """
    更新推理模式接口
    """
    try:
        mode_value = request.mode
        success = translator.set_inference_mode(mode_value)
        
        if success:
            return {
                "success": True,
                "message": f"推理模式已更新为: {mode_value}",
                "mode": mode_value
            }
        else:
            raise HTTPException(status_code=400, detail=f"无法设置推理模式: {mode_value}")
            
    except Exception as e:
        logger.error(f"更新推理模式时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/inference-mode")
async def get_inference_mode():
    """
    获取当前推理模式接口
    """
    try:
        current_mode = translator.get_inference_mode()
        return {
            "success": True,
            "mode": current_mode
        }
    except Exception as e:
        logger.error(f"获取推理模式时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """
    获取配置信息接口
    """
    try:
        config = translator.get_config()
        return {
            "success": True,
            "config": config
        }
    except Exception as e:
        logger.error(f"获取配置时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config")
async def update_config(request: Request):
    """
    更新配置信息接口
    """
    try:
        data = await request.json()
        result = translator.update_config(data)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        logger.error(f"更新配置时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cpu-status")
async def get_cpu_status():
    """
    获取CPU使用状态接口
    """
    try:
        cpu_info = {
            "available": True, 
            "used": True, 
            "type": "CPU",
            "inference_mode": "cpu"
        }
        
        return {
            "success": True,
            "cpu_info": cpu_info,
            "current_mode": translator.get_inference_mode()
        }
    except Exception as e:
        logger.error(f"获取CPU状态时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/detailed-cpu-info")
async def get_detailed_cpu_info():
    """
    获取详细的CPU信息接口
    """
    try:
        # 获取翻译器的CPU利用率信息
        cpu_utilization = translator.get_gpu_utilization()  # 返回CPU相关信息
        
        return {
            "success": True,
            "cpu_info": cpu_utilization,
            "current_mode": translator.get_inference_mode(),
            "model_loaded": hasattr(translator, 'llm_instance') and translator.llm_instance is not None
        }
    except Exception as e:
        logger.error(f"获取详细CPU信息时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def get_models():
    """
    获取模型文件夹中的模型列表
    """
    try:
        result = translator.get_models_list()
        if result["success"]:
            return {
                "success": True,
                "models": result["models"],
                "model_dir": result["model_dir"]
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "获取模型列表失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模型列表时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/switch-model")
async def switch_model(request: Request):
    """
    切换模型接口
    """
    try:
        data = await request.json()
        model_name = data.get("model_name")
        
        if not model_name:
            raise HTTPException(status_code=400, detail="缺少 model_name 参数")
        
        result = translator.switch_model(model_name)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "model_path": result["model_path"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "切换模型失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换模型时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-translate-files")
async def batch_translate_files(request: BatchFileTranslationRequest):
    """
    批量翻译文件接口
    """
    try:
        import os
        from pathlib import Path
        
        results = []
        total_files = len(request.file_paths)
        
        for idx, file_path in enumerate(request.file_paths):
            try:
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": "文件不存在"
                    })
                    continue
                
                # 只处理.txt文件
                if not file_path.lower().endswith('.txt'):
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": "只支持.txt文件"
                    })
                    continue
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": "文件为空"
                    })
                    continue
                
                # 翻译内容
                translation_result = await translator.translate(
                    text=content,
                    source_lang=request.source_lang,
                    target_lang=request.target_lang,
                    provider=request.provider
                )
                
                if not translation_result.get("success"):
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": translation_result.get("error", "翻译失败")
                    })
                    continue
                
                translated_text = translation_result.get("translated_text", "")
                
                # 确定保存路径
                if request.save_mode == "replace":
                    save_path = file_path
                else:  # save_as
                    if not request.save_path:
                        results.append({
                            "file_path": file_path,
                            "success": False,
                            "error": "另存为模式下需要指定保存路径"
                        })
                        continue
                    
                    # 获取原文件名
                    original_filename = os.path.basename(file_path)
                    # 生成新文件名（添加_translated后缀）
                    name, ext = os.path.splitext(original_filename)
                    new_filename = f"{name}_translated{ext}"
                    save_path = os.path.join(request.save_path, new_filename)
                
                # 保存翻译后的内容
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(translated_text)
                
                results.append({
                    "file_path": file_path,
                    "save_path": save_path,
                    "success": True,
                    "progress": (idx + 1) / total_files * 100
                })
                
            except Exception as e:
                logger.error(f"翻译文件 {file_path} 时出错: {str(e)}")
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "error": str(e)
                })
        
        # 统计结果
        success_count = sum(1 for r in results if r.get("success"))
        fail_count = len(results) - success_count
        
        return {
            "success": True,
            "total": total_files,
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"批量翻译文件时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 如果直接运行此文件，则启动服务器
    uvicorn.run(
        "translation_api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # 生产环境中禁用热重载
        log_level="info"
    )