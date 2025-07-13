# 多智能体聊天系统前端

## 🚀 快速启动

### 1. 安装依赖
```bash
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```

前端将在 http://localhost:3000 启动

## 📋 功能特性

- 🤖 多智能体聊天界面
- 📁 文件上传和知识库管理
- 💬 实时对话和历史记录
- 🎨 现代化UI设计
- 📱 响应式布局

## 🔧 配置说明

### 后端API配置
前端通过代理连接到FastAPI后端：
- 开发环境：http://localhost:8000
- 生产环境：需要修改 `vite.config.js` 中的代理配置

### 支持的文件格式
- PDF (.pdf)
- 文本文件 (.txt)
- Word文档 (.docx)
- Markdown (.md)

## 🎯 使用指南

### 1. 启动后端
```bash
cd ../  # 回到week2_homework目录
uvicorn main:app --reload
```

### 2. 启动前端
```bash
npm run dev
```

### 3. 使用功能
- 选择模型和提供商
- 输入会话ID或新建会话
- 上传文档到知识库
- 开始对话

## 🛠️ 技术栈

- Vue 3
- Element Plus
- Axios
- Vite

## 📁 项目结构

```
frontend/
├── src/
│   ├── App.vue          # 主组件
│   └── main.js          # 入口文件
├── index.html           # HTML模板
├── package.json         # 依赖配置
├── vite.config.js       # Vite配置
└── README.md           # 说明文档
``` 