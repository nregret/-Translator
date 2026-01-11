开发协议（请严格遵守）：

严禁修改 Rust 代码：不要动 src-tauri/src/lib.rs 或 main.rs。我已经调通了 Rust 启动 Python 后台的逻辑，任何改动都会导致路径崩溃。

严禁修改 Tauri 配置：不要改动 tauri.conf.json 里的 bundle、resources 或 security 配置。

只允许编辑以下内容：

Python 逻辑：位于 resources/backend/ 下的 .py 文件。

前端代码：位于 src/ 下的 Vue/React/HTML 文件。

交互方式：

Python 后台请使用 FastAPI 暴露接口，默认地址为 127.0.0.1:8000。

前端通过 fetch 与后台通信。 现在你的任务是写一个能够使用python调用大语言翻译模型的脚本