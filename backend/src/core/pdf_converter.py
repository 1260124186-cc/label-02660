"""
PDF转图片模块
使用 pdf2image 将PDF文件转换为图片列表
"""
import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from PIL import Image

logger = logging.getLogger(__name__)


class PDFConverter:
    """PDF文件转图片转换器"""

    DEFAULT_DPI = 300
    DEFAULT_FORMAT = "png"

    def __init__(self, dpi: int = DEFAULT_DPI, output_format: str = DEFAULT_FORMAT):
        self.dpi = dpi
        self.output_format = output_format
        self._check_dependencies()

    def _check_dependencies(self):
        """检查 poppler 依赖"""
        try:
            from pdf2image import convert_from_path
            self._convert_func = convert_from_path
            logger.info("pdf2image 依赖检查通过")
        except ImportError:
            logger.error("pdf2image 未安装，请执行: pip install pdf2image")
            raise
        except Exception as e:
            logger.warning(f"pdf2image 加载警告: {e}")

    def convert_to_images(self, pdf_path: str, output_dir: Optional[str] = None) -> List[str]:
        """
        将PDF文件转换为图片
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录，为None时使用临时目录
        Returns:
            转换后的图片路径列表
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"PDF文件不存在: {pdf_path}")
            return []

        if not pdf_path.suffix.lower() == ".pdf":
            logger.warning(f"文件不是PDF格式: {pdf_path}")
            return []

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="cert_ocr_")
        else:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

        try:
            images = self._convert_func(
                str(pdf_path),
                dpi=self.dpi,
                fmt=self.output_format,
                output_folder=output_dir,
                paths_only=False,
            )

            saved_paths = []
            stem = pdf_path.stem
            for idx, img in enumerate(images):
                filename = f"{stem}_page_{idx + 1}.{self.output_format}"
                save_path = Path(output_dir) / filename
                img.save(str(save_path))
                saved_paths.append(str(save_path))
                logger.debug(f"PDF页面 {idx + 1} 已转换: {save_path}")

            logger.info(f"PDF转换完成: {pdf_path} -> {len(saved_paths)} 页")
            return saved_paths

        except Exception as e:
            logger.error(f"PDF转换失败 [{pdf_path}]: {e}")
            return []

    def convert_single_page(self, pdf_path: str, page_num: int = 1,
                            output_dir: Optional[str] = None) -> Optional[str]:
        """
        转换PDF的单个页面
        Args:
            pdf_path: PDF文件路径
            page_num: 页码(从1开始)
            output_dir: 输出目录
        Returns:
            转换后的图片路径
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return None

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="cert_ocr_")

        try:
            images = self._convert_func(
                str(pdf_path),
                dpi=self.dpi,
                fmt=self.output_format,
                first_page=page_num,
                last_page=page_num,
            )

            if images:
                filename = f"{pdf_path.stem}_page_{page_num}.{self.output_format}"
                save_path = Path(output_dir) / filename
                images[0].save(str(save_path))
                logger.info(f"PDF单页转换完成: 第{page_num}页 -> {save_path}")
                return str(save_path)

        except Exception as e:
            logger.error(f"PDF单页转换失败: {e}")

        return None

    @staticmethod
    def is_pdf(file_path: str) -> bool:
        """判断文件是否为PDF"""
        return Path(file_path).suffix.lower() == ".pdf"

    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """获取PDF页数"""
        try:
            from pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(str(pdf_path))
            return info.get("Pages", 0)
        except Exception as e:
            logger.error(f"获取PDF页数失败: {e}")
            return 0
