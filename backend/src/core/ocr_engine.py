"""
OCR识别引擎模块
支持 PaddleOCR 和 Tesseract 双引擎，默认使用 PaddleOCR
"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class OCREngine:
    """OCR识别引擎，封装 PaddleOCR"""

    def __init__(self, engine_type: str = "paddle", lang: str = "ch"):
        self.engine_type = engine_type
        self.lang = lang
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        """延迟初始化OCR引擎"""
        if self.engine_type == "paddle":
            try:
                from paddleocr import PaddleOCR
                self._engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    show_log=False,
                    use_gpu=False,
                )
                logger.info("PaddleOCR 引擎初始化成功")
            except ImportError:
                logger.error("PaddleOCR 未安装，请执行: pip install paddleocr paddlepaddle")
                raise
        else:
            raise ValueError(f"不支持的OCR引擎类型: {self.engine_type}")

    def recognize(self, image_input) -> List[dict]:
        """
        对图片进行OCR识别
        Args:
            image_input: 图片路径(str/Path) 或 numpy数组 或 PIL.Image
        Returns:
            识别结果列表，每项包含 text, confidence, bbox
        """
        img = self._load_image(image_input)
        if img is None:
            logger.warning(f"无法加载图片: {image_input}")
            return []

        try:
            results = self._engine.ocr(img, cls=True)
            return self._parse_results(results)
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return []

    def recognize_region(self, image_input, region: dict) -> List[dict]:
        """
        对图片指定区域进行OCR识别
        Args:
            image_input: 图片输入
            region: 区域字典 {x, y, w, h} 百分比或像素值
        Returns:
            识别结果列表
        """
        img = self._load_image(image_input)
        if img is None:
            return []

        h, w = img.shape[:2]
        x = int(region.get("x", 0) * w) if region.get("x", 0) <= 1 else int(region["x"])
        y = int(region.get("y", 0) * h) if region.get("y", 0) <= 1 else int(region["y"])
        rw = int(region.get("w", 1) * w) if region.get("w", 1) <= 1 else int(region["w"])
        rh = int(region.get("h", 1) * h) if region.get("h", 1) <= 1 else int(region["h"])

        cropped = img[y:y + rh, x:x + rw]
        if cropped.size == 0:
            logger.warning(f"裁剪区域为空: {region}")
            return []

        return self.recognize(cropped)

    def _load_image(self, image_input) -> Optional[np.ndarray]:
        """统一加载图片为 numpy 数组"""
        if isinstance(image_input, np.ndarray):
            return image_input
        if isinstance(image_input, Image.Image):
            return cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        if isinstance(image_input, (str, Path)):
            path = str(image_input)
            img = cv2.imread(path)
            if img is None:
                img = cv2.imdecode(
                    np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR
                )
            return img
        return None

    def _parse_results(self, results: list) -> List[dict]:
        """解析PaddleOCR返回结果为统一格式"""
        parsed = []
        if not results or not results[0]:
            return parsed

        for line in results[0]:
            bbox = line[0]
            text = line[1][0]
            confidence = line[1][1]
            parsed.append({
                "text": text.strip(),
                "confidence": round(confidence, 4),
                "bbox": bbox,
            })

        parsed.sort(key=lambda x: (x["bbox"][0][1], x["bbox"][0][0]))
        logger.debug(f"OCR识别到 {len(parsed)} 条文本")
        return parsed

    def preprocess_image(self, image_input) -> np.ndarray:
        """图像预处理，提升识别率"""
        img = self._load_image(image_input)
        if img is None:
            raise ValueError("无法加载图片进行预处理")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        result = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)

        logger.debug("图像预处理完成")
        return result
