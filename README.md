# 比赛证书自动识别管理系统

## How to Run

```bash
# 克隆项目
git clone <repo-url>
cd label-02660

# 一键启动（需要 Docker 和 Docker Compose）
docker compose up --build -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

启动完成后访问：
- 管理后台：http://localhost:8081
- 后端 API：http://localhost:8083/docs（Swagger 文档）

停止服务：
```bash
docker compose down
```

## Services

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend-admin | 8081 | Vue3 管理后台（Nginx 托管） |
| backend | 8083 | FastAPI 后端 API（PaddleOCR 引擎） |

## 测试账号

| 用户名 | 密码 |
|--------|------|
| admin | admin123 |

登录后可使用全部功能。测试证书文件位于 `frontend-admin/test-files/` 目录下。

## 题目内容

我需要开发一个比赛证书自动识别管理系统，实现以下功能：
1、具有UI界面，能让用户指定证书存放所在文件夹；能让用户选择不同类型的比赛证书样本自动生成yaml文件保存在模版文件夹中；能让用户对比较复杂的证书格式通过交互方式生成yaml文件并保存
2、证书格式包括pdf、jpg、png等格式，用户点击开始整理按钮后能自动将pdf文件转成图片格式并进行OCR识别提取证书信息，包括：1、获奖时间，包括年月日，统一以“20250501”的格式输出。如果证书上只有年月，则自动默认为当月1号；2、获奖名称；3、授奖单位（依证书落款按顺序填写）；4、获奖等级；5、指导老师（全部）；6、获奖学生(全部)。所有信息提取后自动保存到指定的excel文件中。
3、UI上具有保存选项，包括指定输出位置、以追加方式还是以覆盖方式写入Excel文件的选项。识别完成后按照指定的方式输出。
4、具有很高的识别成功率和信息提取准确率，能有较快的处理速度；
5、基于Python 生态实现
OCR 引擎：PaddleOCR（中文支持好、开源、高精度） 或 Tesseract（轻量）
PDF 转图像：pdf2image（依赖 Poppler）
图像处理：OpenCV / Pillow
模板匹配/分类：可先用文件名、主办方关键词、或简单图像哈希聚类；进阶可用 CNN 分类
数据结构化：pandas 写 Excel
流程编排：Python 脚本 + 配置文件（YAML/JSON）

---

## 系统架构

```
label-02660/
├── docker-compose.yml              # Docker 编排
├── .gitignore
├── README.md
├── docs/
│   └── project_design.md           # 项目设计文档
├── backend/                        # 后端服务 (FastAPI + PaddleOCR)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     # FastAPI 入口
│   ├── templates/                  # YAML 模板目录
│   │   ├── general.yaml
│   │   └── math_competition.yaml
│   └── src/
│       ├── api/
│       │   ├── cert_api.py         # 证书识别 API
│       │   └── template_api.py     # 模板管理 API
│       ├── core/
│       │   ├── ocr_engine.py       # OCR 引擎 (PaddleOCR)
│       │   ├── pdf_converter.py    # PDF 转图片
│       │   ├── template_manager.py # 模板管理
│       │   ├── info_extractor.py   # 信息提取
│       │   ├── excel_exporter.py   # Excel 导出
│       │   └── processor.py        # 核心流程编排
│       └── utils/
│           └── logger.py
└── frontend-admin/                 # 管理后台 (Vue3 + Element Plus)
    ├── Dockerfile
    ├── nginx.conf
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── test-files/                 # 测试证书文件
    │   ├── 测试证书_数学建模竞赛一等奖.png
    │   └── 测试证书_英语演讲比赛二等奖.png
    └── src/
        ├── App.vue
        ├── main.js
        ├── api/
        │   ├── cert.js             # 证书 API
        │   ├── request.js          # Axios 封装
        │   └── template.js         # 模板 API
        ├── stores/
        │   ├── cert.js             # 证书状态管理
        │   ├── template.js         # 模板状态管理
        │   └── user.js             # 用户登录状态
        ├── views/
        │   ├── Login.vue           # 登录页
        │   ├── CertRecognition.vue # 证书识别页
        │   └── TemplateManage.vue  # 模板管理页
        ├── assets/
        │   └── global.scss         # 全局样式
        ├── router/
        │   └── index.js            # 路由配置
        ├── components/
        └── utils/
            └── yaml-lite.js
```

## 技术栈

- **后端**: Python 3.11 + FastAPI + PaddleOCR + pdf2image + OpenCV + pandas
- **前端**: Vue 3 + Vite + Element Plus + Pinia + Axios + SCSS
- **部署**: Docker + Docker Compose + Nginx

## 功能特性

- 📄 支持 PDF / JPG / PNG / BMP / TIFF 格式证书批量识别
- 📁 支持上传文件夹，自动递归扫描子目录中的证书文件
- 🔐 登录认证，Header 展示用户信息及退出登录
- 🔍 PaddleOCR 中文高精度识别引擎
- 📋 YAML 模板系统：自动匹配、手动创建、交互式生成
- 📊 自动提取：获奖时间、名称、单位、等级、指导老师、获奖学生
- 📥 Excel 导出：支持覆盖/追加写入，带专业格式化
- 🐳 Docker 一键部署，跨平台支持 ARM64 + AMD64
