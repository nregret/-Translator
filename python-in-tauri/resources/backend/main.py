import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 导入翻译API应用
from translation_api import app
import uvicorn

if __name__ == "__main__":
    print("Starting Translation API Server...")
    
    # 在主线程中启动FastAPI服务器
    uvicorn.run(
        "translation_api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )