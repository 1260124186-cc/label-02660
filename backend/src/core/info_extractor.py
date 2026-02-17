"""
证书信息提取模块
从OCR识别结果中提取结构化的证书信息
"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# 中文数字映射
CN_NUM_MAP = {
    "零": "0", "〇": "0", "○": "0", "O": "0",
    "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
    "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
}


@dataclass
class CertInfo:
    """证书信息数据类"""
    award_date: str = ""
    award_name: str = ""
    award_org: str = ""
    award_level: str = ""
    teachers: str = ""
    students: str = ""
    source_file: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    def is_valid(self) -> bool:
        """至少有奖项名称或获奖学生才算有效"""
        return bool(self.award_name or self.students)


class InfoExtractor:
    """证书信息提取器"""

    def __init__(self):
        self._cn_year_pattern = re.compile(
            r"[二贰][\s]*[零〇○O\d][\s]*[\d零〇○O一二三四五六七八九][\s]*[\d零〇○O一二三四五六七八九][\s]*年"
        )

    def extract(self, ocr_results: List[dict], template: dict,
                source_file: str = "") -> CertInfo:
        """
        从OCR结果中提取证书信息
        Args:
            ocr_results: OCR识别结果列表 [{text, confidence, bbox}]
            template: 模板配置字典
            source_file: 源文件路径
        Returns:
            CertInfo 数据对象
        """
        texts = [r["text"] for r in ocr_results]
        full_text = "\n".join(texts)
        avg_conf = sum(r.get("confidence", 0) for r in ocr_results) / max(len(ocr_results), 1)

        fields_config = template.get("fields", {})

        info = CertInfo(
            source_file=source_file,
            confidence=round(avg_conf, 4),
        )

        info.award_date = self._extract_date(texts, full_text, fields_config.get("award_date", {}))
        info.award_name = self._extract_award_name(texts, full_text, fields_config.get("award_name", {}))
        info.award_org = self._extract_org(texts, full_text, fields_config.get("award_org", {}))
        info.award_level = self._extract_level(texts, full_text, fields_config.get("award_level", {}))
        info.teachers = self._extract_teachers(texts, full_text, fields_config.get("teachers", {}))
        info.students = self._extract_students(texts, full_text, fields_config.get("students", {}))

        logger.info(f"信息提取完成 [{source_file}]: 日期={info.award_date}, "
                     f"奖项={info.award_name}, 等级={info.award_level}")
        return info

    def _extract_date(self, texts: List[str], full_text: str, config: dict) -> str:
        """提取获奖日期，统一输出为 YYYYMMDD 格式"""
        patterns = config.get("patterns", [
            r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
            r"(\d{4})\s*年\s*(\d{1,2})\s*月",
            r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})",
            r"(\d{4})[-/](\d{1,2})",
        ])

        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                groups = match.groups()
                year = groups[0] if len(groups) > 0 else ""
                month = groups[1] if len(groups) > 1 else "01"
                day = groups[2] if len(groups) > 2 else "01"
                try:
                    return f"{int(year):04d}{int(month):02d}{int(day):02d}"
                except (ValueError, TypeError):
                    continue

        cn_match = self._cn_year_pattern.search(full_text)
        if cn_match:
            cn_date = cn_match.group()
            converted = self._convert_cn_date(cn_date, full_text)
            if converted:
                return converted

        return ""

    def _convert_cn_date(self, cn_date_str: str, full_text: str) -> str:
        """将中文日期转换为数字格式"""
        try:
            digits = ""
            for ch in cn_date_str:
                if ch in CN_NUM_MAP:
                    digits += CN_NUM_MAP[ch]
                elif ch.isdigit():
                    digits += ch

            if len(digits) >= 4:
                year = digits[:4]
            else:
                return ""

            month = "01"
            day = "01"

            month_match = re.search(r"年\s*(\d{1,2}|[一二三四五六七八九十]+)\s*月", full_text)
            if month_match:
                m_str = month_match.group(1)
                if m_str.isdigit():
                    month = m_str
                else:
                    month = self._cn_to_num(m_str)

            day_match = re.search(r"月\s*(\d{1,2}|[一二三四五六七八九十]+)\s*日", full_text)
            if day_match:
                d_str = day_match.group(1)
                if d_str.isdigit():
                    day = d_str
                else:
                    day = self._cn_to_num(d_str)

            return f"{int(year):04d}{int(month):02d}{int(day):02d}"
        except Exception as e:
            logger.debug(f"中文日期转换失败: {e}")
            return ""

    @staticmethod
    def _cn_to_num(cn_str: str) -> str:
        """中文数字转阿拉伯数字(1-31)"""
        if not cn_str:
            return "01"
        if cn_str == "十":
            return "10"
        if cn_str.startswith("十"):
            unit = CN_NUM_MAP.get(cn_str[-1], "0")
            return str(10 + int(unit))
        if cn_str.endswith("十"):
            tens = CN_NUM_MAP.get(cn_str[0], "1")
            return str(int(tens) * 10)
        if len(cn_str) == 3 and "十" in cn_str:
            tens = CN_NUM_MAP.get(cn_str[0], "0")
            unit = CN_NUM_MAP.get(cn_str[2], "0")
            return str(int(tens) * 10 + int(unit))
        if cn_str in CN_NUM_MAP:
            return CN_NUM_MAP[cn_str]
        return "01"

    def _extract_award_name(self, texts: List[str], full_text: str, config: dict) -> str:
        """提取获奖名称"""
        patterns = config.get("patterns", [
            r'荣获["\u201c\u201d]?\s*(.+?)\s*["\u201c\u201d]?\s*(?:奖|称号)',
            r'获得["\u201c\u201d]?\s*(.+?)\s*["\u201c\u201d]?(?:奖|称号|荣誉)',
            r'授予["\u201c\u201d]?\s*(.+?)\s*["\u201c\u201d]?(?:称号|荣誉)',
            r"(.+?(?:竞赛|比赛|大赛|挑战赛|锦标赛|奥林匹克))",
        ])

        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                name = match.group(1).strip()
                name = re.sub(r"[\"\"\"''']", "", name)
                if len(name) >= 2:
                    return name

        competition_keywords = ["竞赛", "比赛", "大赛", "挑战赛", "锦标赛", "奥赛", "奥林匹克", "杯"]
        for text in texts:
            for kw in competition_keywords:
                if kw in text:
                    cleaned = re.sub(r"^\d+[.、]\s*", "", text.strip())
                    if 4 <= len(cleaned) <= 50:
                        return cleaned

        return ""

    def _extract_org(self, texts: List[str], full_text: str, config: dict) -> str:
        """提取授奖单位（按落款顺序）"""
        patterns = config.get("patterns", [
            r"(?:主办[单方]?[位方]?|颁发[单方]?[位方]?|发证[单方]?[位方]?)[：:]\s*(.+)",
        ])

        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                return match.group(1).strip()

        org_keywords = ["部", "厅", "局", "委员会", "协会", "学会", "联合会",
                        "中心", "教育", "科技", "基金会", "组委会"]
        orgs = []
        location_hint = config.get("location_hint", "bottom")

        search_texts = texts
        if location_hint == "bottom":
            start_idx = max(0, len(texts) - len(texts) // 3)
            search_texts = texts[start_idx:]

        for text in search_texts:
            for kw in org_keywords:
                if kw in text:
                    cleaned = text.strip()
                    cleaned = re.sub(r"^\d{4}年.*$", "", cleaned)
                    cleaned = re.sub(r"[（(].*?[）)]", "", cleaned).strip()
                    if cleaned and len(cleaned) >= 3 and cleaned not in orgs:
                        orgs.append(cleaned)
                    break

        return "、".join(orgs) if orgs else ""

    def _extract_level(self, texts: List[str], full_text: str, config: dict) -> str:
        """提取获奖等级"""
        patterns = config.get("patterns", [
            r"(特等奖|一等奖|二等奖|三等奖|优秀奖|金奖|银奖|铜奖|优胜奖)",
            r"(第[一二三四五六七八九十\d]+名)",
            r"(国家级|省级|市级|区级|校级)",
            r"(冠军|亚军|季军)",
        ])

        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_teachers(self, texts: List[str], full_text: str, config: dict) -> str:
        """提取指导老师"""
        patterns = config.get("patterns", [
            r"指导[老教]师[：:]\s*(.+?)(?:\n|$|指导|学生|选手)",
            r"指导[老教]师\s+(.+?)(?:\n|$)",
            r"辅导[老教]师[：:]\s*(.+?)(?:\n|$)",
            r"指导[老教]师[：:]?\s*(.+)",
        ])

        separator = config.get("separator", r"[、,，\s]+")

        for pattern in patterns:
            match = re.search(pattern, full_text, re.MULTILINE)
            if match:
                raw = match.group(1).strip()
                raw = re.sub(r"[（(].*?[）)]", "", raw)
                names = re.split(separator, raw)
                names = [n.strip() for n in names if n.strip() and 2 <= len(n.strip()) <= 5]
                if names:
                    return "、".join(names)

        for text in texts:
            if "指导" in text and ("老师" in text or "教师" in text):
                raw = re.sub(r".*(?:指导[老教]师)[：:]*\s*", "", text)
                names = re.split(separator, raw)
                names = [n.strip() for n in names if n.strip() and 2 <= len(n.strip()) <= 5]
                if names:
                    return "、".join(names)

        return ""

    def _extract_students(self, texts: List[str], full_text: str, config: dict) -> str:
        """提取获奖学生"""
        patterns = config.get("patterns", [
            r"(?:学生|选手|参赛者|获奖者|获奖学生)[：:]\s*(.+?)(?:\n|$)",
            r"(?:同学|学员)\s*(.+?)(?:\n|$)",
        ])

        separator = config.get("separator", r"[、,，\s]+")

        for pattern in patterns:
            match = re.search(pattern, full_text, re.MULTILINE)
            if match:
                raw = match.group(1).strip()
                names = re.split(separator, raw)
                names = [n.strip() for n in names if n.strip() and 2 <= len(n.strip()) <= 5]
                if names:
                    return "、".join(names)

        name_patterns = [
            r"兹?\s*(?:证明|授予)?\s*([\u4e00-\u9fa5]{2,4}(?:[、,，\s]+[\u4e00-\u9fa5]{2,4})*)\s*(?:等\s*)?同学",
            r"([\u4e00-\u9fa5]{2,4}(?:[、,，\s]+[\u4e00-\u9fa5]{2,4})*)\s*(?:等\s*)?(?:同学|学生|选手)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, full_text)
            if match:
                raw = match.group(1).strip()
                names = re.split(r"[、,，\s]+", raw)
                names = [m.strip() for m in names if 2 <= len(m.strip()) <= 4]
                if names:
                    return "、".join(list(dict.fromkeys(names)))

        return ""
