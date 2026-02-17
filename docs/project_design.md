# 比赛证书自动识别管理系统 - 项目设计文档

## 1. 系统架构

```mermaid
flowchart TD
    A[用户界面 PyQt5] --> B[控制层 MainController]
    B --> C[PDF转换模块 pdf2image]
    B --> D[OCR识别引擎 PaddleOCR]
    B --> E[模板管理模块 YAML]
    B --> F[信息提取模块 Extractor]
    B --> G[Excel导出模块 pandas]
    C --> D
    D --> F
    E --> F
    F --> G

    subgraph 核心引擎
        C
        D
        E
        F
    end

    subgraph 数据输出
        G --> H[Excel文件]
    end
```

## 2. 模块设计

```mermaid
classDiagram
    class MainWindow {
        -cert_folder_path: str
        -output_path: str
        -write_mode: str
        +select_folder()
        +select_output()
        +start_process()
        +manage_templates()
    }

    class CertProcessor {
        -ocr_engine: OCREngine
        -template_mgr: TemplateManager
        -extractor: InfoExtractor
        +process_folder(path)
        +process_single(file)
    }

    class OCREngine {
        -paddle_ocr: PaddleOCR
        +recognize(image) list~str~
    }

    class PDFConverter {
        +convert_to_images(pdf_path) list~Image~
    }

    class TemplateManager {
        -template_dir: str
        +load_template(name) dict
        +save_template(name, config)
        +list_templates() list
        +generate_from_sample(image) dict
    }

    class InfoExtractor {
        +extract(ocr_texts, template) CertInfo
        -extract_date(texts) str
        -extract_award_name(texts) str
        -extract_org(texts) str
        -extract_level(texts) str
        -extract_teachers(texts) list
        -extract_students(texts) list
    }

    class ExcelExporter {
        +export(data, path, mode)
    }

    MainWindow --> CertProcessor
    CertProcessor --> OCREngine
    CertProcessor --> PDFConverter
    CertProcessor --> TemplateManager
    CertProcessor --> InfoExtractor
    CertProcessor --> ExcelExporter
```

## 3. 数据流 ER 图

```mermaid
erDiagram
    CERTIFICATE {
        string file_path PK
        string file_type
        string template_name
    }
    CERT_INFO {
        string award_date
        string award_name
        string award_org
        string award_level
        string teachers
        string students
        string source_file
    }
    TEMPLATE {
        string name PK
        string cert_type
        string regions JSON
        string keywords JSON
    }
    CERTIFICATE ||--|| CERT_INFO : "识别生成"
    TEMPLATE ||--o{ CERTIFICATE : "匹配应用"
```

## 4. 接口清单

| 模块 | 方法 | 说明 |
|------|------|------|
| PDFConverter | `convert_to_images(pdf_path)` | PDF转图片列表 |
| OCREngine | `recognize(image_path)` | OCR识别返回文本列表 |
| TemplateManager | `load_template(name)` | 加载YAML模板 |
| TemplateManager | `save_template(name, config)` | 保存YAML模板 |
| TemplateManager | `list_templates()` | 列出所有模板 |
| TemplateManager | `generate_from_sample(image, regions)` | 交互式生成模板 |
| InfoExtractor | `extract(ocr_texts, template)` | 从OCR文本提取结构化信息 |
| ExcelExporter | `export(data, path, mode)` | 导出Excel(追加/覆盖) |
| CertProcessor | `process_folder(path)` | 批量处理文件夹 |

## 5. UI/UX 规范

- **主色调**: `#2563EB` (蓝) / `#1E40AF` (深蓝)
- **辅助色**: `#10B981` (成功绿) / `#EF4444` (错误红) / `#F59E0B` (警告黄)
- **背景色**: `#F1F5F9` (浅灰蓝)
- **卡片背景**: `#FFFFFF`，圆角 `8px`，阴影 `0 2px 8px rgba(0,0,0,0.08)`
- **字体**: 系统默认，标题 `16px bold`，正文 `14px`，辅助 `12px`
- **间距**: 统一 `8px / 16px / 24px` 递进
- **按钮**: 圆角 `6px`，hover 加深 10%，点击有 loading 动画
- **反馈**: 操作成功/失败均有 Toast 提示
