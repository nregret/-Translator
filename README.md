# SimpleTauri Translator | 轻量级智能翻译专家

![SimpleTauri Logo](./python-in-tauri/src-tauri/icons/128x128.png)
*(这里可以放置一张应用的 LOGO 图)*

SimpleTauri 是一款基于 **Tauri (Rust)** 和 **Vue 3** 构建的现代化桌面翻译工具。它结合了前端的极致性能与后端 Python 的强大处理能力，支持文本 API 翻译、批量文件翻译，并集成本地 AI 模型，旨在提供私密、高效、流畅的翻译体验。

---

## ✨ 核心特性

- 🚀 **极致性能**：采用 Rust 构建后端核心，Tauri 框架让应用既轻量又快速。
- 🤖 **本地模型支持**：支持集成本地 LLM（大语言模型），无需联网即可进行高质量翻译，保护隐私。
- 📄 **批量文件翻译**：一键处理多个文档，支持常见文件格式。
- 🎨 **现代 UI 设计**：精致的侧边栏布局，基于 Vue 3 打造的流畅交互。
- 🐍 **Python 增强**：利用 Python 生态处理复杂的文本解析与 AI 推理。

---

## 📸 应用截图

![首页](./example/1.png)

![设置](./example/2.png)

---

## 🚀 快速开始

### 环境依赖
- [Rust](https://www.rust-lang.org/)
- [Node.js](https://nodejs.org/)
- [Python 3.10+](https://www.python.org/)

### 安装与运行

1. **克隆项目**
   ```bash
   git clone https://github.com/nregret/-Translator.git
   cd -Translator
   ```

2. **安装依赖**
   ```bash
   cd python-in-tauri
   npm install
   ```

3. **启动开发服务器**
   ```bash
   npm run tauri dev
   ```

4. **构建正式版**
   ```bash
   npm run tauri build
   ```

---

## 🛠️ 技术栈

| 组件 | 技术 |
| :--- | :--- |
| **壳体/后端 (Core)** | [Tauri](https://tauri.app/) (Rust) |
| **前端 (UI)** | [Vue 3](https://vuejs.org/) + [Vite](https://vitejs.dev/) |
| **AI 处理** | Python + Local LLM |
| **通信** | Tauri Command (Invoke) |

---

## 📂 项目结构

```text
SimpleTauri/
├── python-in-tauri/        # 主要开发目录
│   ├── src/                # Vue 3 前端源代码
│   ├── src-tauri/          # Tauri Rust 后端代码
│   └── resources/          # 存放 Python 运行环境与模型
└── .gitignore              # 忽略大型二进制文件
```

---

## 🤝 贡献

如果你有任何好的想法或发现了 Bug，欢迎提交 Issue 或 Pull Request！

## 📄 开源协议

[MIT License](LICENSE)
