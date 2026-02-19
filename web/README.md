# MD2WeChat Web 批量上传工具

基于 Vue 3 + FastAPI 的 Web 界面，支持批量上传 Markdown 文档到微信公众号草稿箱。

## 功能特性

- 拖拽/点击上传多个 Markdown 文件
- 串行上传，自动跳过失败项
- 可视化配置面板（样式、评论等）
- 实时上传进度和结果展示
- 错误处理和重试机制

## 快速开始

### 1. 安装依赖

```bash
# 后端依赖
pip install -r backend/requirements.txt

# 前端依赖
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
# 方式一：同时启动前后端（推荐开发使用）
# 终端 1：启动后端
cd backend
python main.py

# 终端 2：启动前端
cd frontend
npm run dev
```

然后访问 http://localhost:3000

### 3. 生产环境部署

```bash
# 构建前端
cd frontend
npm run build

# 启动后端（自动托管静态文件）
cd ../backend
python main.py
```

然后访问 http://localhost:8000

## 项目结构

```
web/
├── frontend/              # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConfigPanel.vue      # 配置面板
│   │   │   ├── FileUploader.vue     # 文件上传
│   │   │   ├── FileList.vue         # 文件列表
│   │   │   └── UploadResults.vue    # 上传结果
│   │   ├── App.vue
│   │   └── api.js
│   └── package.json
└── backend/
    ├── main.py            # FastAPI 后端
    └── requirements.txt
```

## 环境变量

确保在项目根目录有 `.env` 文件：

```bash
WECHAT_APPID=your_appid
WECHAT_APP_SECRET=your_secret
```

## 使用说明

1. 选择要上传的 Markdown 文件（可多选）
2. 在左侧配置面板设置样式、评论等选项
3. 点击"开始批量上传"按钮
4. 等待上传完成，查看结果报告

每个文件独立处理，失败不会中断其他文件的上传。
