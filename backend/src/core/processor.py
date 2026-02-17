"""
证书处理器 - 核心流程编排
协调 PDF转换、OCR识别、模板匹配、信息提取的完整流程
"""
import logging
import os
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass

from src.core.ocr_engine import OCREngine
from src.core.pdf_converter import PDFConverter
from src.core.template_manager import TemplateManager
from src.core.info_extractor import InfoExtractor, CertInfo
from src.core.excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
SUPPORTED_PDF_EXT = ".pdf"


@dataclass
class ProcessResult:
    """处理结果"""
    total: int = 0
    success: int = 0
    failed: int = 0
    results: List[CertInfo] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.errors is None:
            self.errors = []


class CertProcessor:
    """证书处理器"""

    def __init__(self, template_dir: str = "templates"):
        self.ocr_engine: Optional[OCREngine] = None
        self.pdf_converter: Optional[PDFConverter] = None
        self.template_mgr = TemplateManager(template_dir)
        self.extractor = InfoExtractor()
        self.exporter = ExcelExporter()
        self._progress_callback: Optional[Callable] = None
        self._is_cancelled = False

    def init_engines(self):
        """初始化OCR和PDF引擎（耗时操作，单独调用）"""
        if self.ocr_engine is None:
            logger.info("正在初始化OCR引擎...")
            self.ocr_engine = OCREngine()
        if self.pdf_converter is None:
            logger.info("正在初始化PDF转换器...")
            self.pdf_converter = PDFConverter()

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数 callback(current, total, filename, status)"""
        self._progress_callback = callback

    def cancel(self):
        """取消处理"""
        self._is_cancelled = True
        logger.info("用户取消处理")

    def reset_cancel(self):
        """重置取消状态"""
        self._is_cancelled = False

    def process_folder(self, folder_path: str, output_path: str,
                       write_mode: str = "overwrite") -> ProcessResult:
        """
        批量处理文件夹中的证书文件
        Args:
            folder_path: 证书文件夹路径
            output_path: Excel输出路径
            write_mode: 写入模式 overwrite/append
        Returns:
            ProcessResult
        """
        self.reset_cancel()
        self.init_engines()

        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            logger.error(f"文件夹不存在: {folder_path}")
            return ProcessResult(errors=[f"文件夹不存在: {folder_path}"])

        files = self._scan_files(folder)
        if not files:
            logger.warning(f"文件夹中没有可处理的文件: {folder_path}")
            return ProcessResult(errors=["文件夹中没有可处理的证书文件"])

        result = ProcessResult(total=len(files))
        logger.info(f"开始处理 {len(files)} 个文件")

        for idx, file_path in enumerate(files):
            if self._is_cancelled:
                logger.info("处理已取消")
                break

            self._report_progress(idx, len(files), file_path.name, "处理中")

            try:
                cert_info = self.process_single(str(file_path))
                if cert_info and cert_info.is_valid():
                    result.results.append(cert_info)
                    result.success += 1
                    self._report_progress(idx + 1, len(files), file_path.name, "成功")
                else:
                    result.failed += 1
                    result.errors.append(f"信息提取不完整: {file_path.name}")
                    self._report_progress(idx + 1, len(files), file_path.name, "提取不完整")
            except Exception as e:
                result.failed += 1
                error_msg = f"处理失败 [{file_path.name}]: {str(e)}"
                result.errors.append(error_msg)
                logger.error(error_msg)
                self._report_progress(idx + 1, len(files), file_path.name, f"失败: {e}")

        # 导出Excel
        if result.results:
            export_data = [info.to_dict() for info in result.results]
            success = self.exporter.export(export_data, output_path, write_mode)
            if success:
                logger.info(f"结果已导出到: {output_path}")
            else:
                result.errors.append("Excel导出失败")

        logger.info(f"处理完成: 总计{result.total}, 成功{result.success}, 失败{result.failed}")
        return result

    def process_single(self, file_path: str) -> Optional[CertInfo]:
        """
        处理单个证书文件
        Args:
            file_path: 文件路径
        Returns:
            CertInfo 或 None
        """
        self.init_engines()
        file_path = Path(file_path)
        ext = file_path.suffix.lower()

        logger.info(f"处理文件: {file_path.name}")

        # PDF先转图片
        if ext == SUPPORTED_PDF_EXT:
            image_paths = self.pdf_converter.convert_to_images(str(file_path))
            if not image_paths:
                logger.error(f"PDF转换失败: {file_path}")
                return None
            # 处理所有页面，合并结果
            all_ocr_results = []
            for img_path in image_paths:
                ocr_results = self.ocr_engine.recognize(img_path)
                all_ocr_results.extend(ocr_results)
        elif ext in SUPPORTED_IMAGE_EXTS:
            # 图像预处理 + OCR
            preprocessed = self.ocr_engine.preprocess_image(str(file_path))
            all_ocr_results = self.ocr_engine.recognize(preprocessed)
            # 如果预处理后识别结果少，尝试原图
            if len(all_ocr_results) < 3:
                raw_results = self.ocr_engine.recognize(str(file_path))
                if len(raw_results) > len(all_ocr_results):
                    all_ocr_results = raw_results
        else:
            logger.warning(f"不支持的文件格式: {ext}")
            return None

        if not all_ocr_results:
            logger.warning(f"OCR未识别到文本: {file_path}")
            return None

        # 模板匹配
        texts = [r["text"] for r in all_ocr_results]
        template = self.template_mgr.match_template(texts)

        # 信息提取
        cert_info = self.extractor.extract(all_ocr_results, template, str(file_path.name))
        return cert_info

    def _scan_files(self, folder: Path) -> List[Path]:
        """扫描文件夹中的可处理文件"""
        files = []
        all_exts = SUPPORTED_IMAGE_EXTS | {SUPPORTED_PDF_EXT}
        for f in sorted(folder.iterdir()):
            if f.is_file() and f.suffix.lower() in all_exts:
                files.append(f)
        logger.info(f"扫描到 {len(files)} 个可处理文件")
        return files

    def _report_progress(self, current: int, total: int, filename: str, status: str):
        """报告进度"""
        if self._progress_callback:
            try:
                self._progress_callback(current, total, filename, status)
            except Exception:
                pass
