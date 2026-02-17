"""
模板管理模块
管理证书识别模板(YAML格式)，支持创建、加载、编辑模板
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional
from copy import deepcopy

import yaml

logger = logging.getLogger(__name__)

# 默认模板结构
DEFAULT_TEMPLATE = {
    "name": "",
    "description": "",
    "cert_type": "general",
    "keywords": [],
    "fields": {
        "award_date": {
            "patterns": [
                r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日",
                r"\d{4}\s*年\s*\d{1,2}\s*月",
                r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
                r"\d{4}[-/]\d{1,2}",
                r"二[○〇零O]\S{1,2}年\S{1,3}月",
            ],
            "region": None,
            "priority": 1,
        },
        "award_name": {
            "patterns": [
                r'荣获["\u201c\u201d]?(.+?)["\u201c\u201d]?奖',
                r'获得["\u201c\u201d]?(.+?)["\u201c\u201d]?',
                r'授予["\u201c\u201d]?(.+?)["\u201c\u201d]?称号',
                r"(.+?(?:竞赛|比赛|大赛|挑战赛|锦标赛))",
                r"(.+?(?:一等奖|二等奖|三等奖|特等奖|金奖|银奖|铜奖|优秀奖))",
            ],
            "region": None,
            "priority": 2,
        },
        "award_org": {
            "patterns": [
                r"(?:主办[单方]?[位方]?|颁发[单方]?[位方]?|发证[单方]?[位方]?)[：:]\s*(.+)",
                r"([\u4e00-\u9fa5]+(?:部|厅|局|委|会|协会|学会|联合会|中心))",
            ],
            "region": {"x": 0.3, "y": 0.75, "w": 0.5, "h": 0.25},
            "priority": 3,
            "location_hint": "bottom",
        },
        "award_level": {
            "patterns": [
                r"(特等奖|一等奖|二等奖|三等奖|优秀奖|金奖|银奖|铜奖)",
                r"(第[一二三四五六七八九十]+名)",
                r"(国家级|省级|市级|区级|校级)",
                r"(冠军|亚军|季军)",
            ],
            "region": None,
            "priority": 4,
        },
        "teachers": {
            "patterns": [
                r"指导[老教]师[：:]\s*(.+)",
                r"指导[老教]师\s+(.+)",
                r"辅导[老教]师[：:]\s*(.+)",
            ],
            "region": None,
            "priority": 5,
            "separator": r"[、,，\s]+",
        },
        "students": {
            "patterns": [
                r"(?:学生|选手|参赛者|获奖者)[：:]\s*(.+)",
                r"(?:同学|学员)\s+(.+)",
            ],
            "region": None,
            "priority": 6,
            "separator": r"[、,，\s]+",
            "name_hint": "center_top",
        },
    },
}


class TemplateManager:
    """证书模板管理器"""

    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, dict] = {}
        logger.info(f"模板管理器初始化，模板目录: {self.template_dir}")

    def list_templates(self) -> List[dict]:
        """
        列出所有可用模板
        Returns:
            模板信息列表 [{name, description, cert_type, path}]
        """
        templates = []
        for f in self.template_dir.glob("*.yaml"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = yaml.safe_load(fp)
                templates.append({
                    "name": data.get("name", f.stem),
                    "description": data.get("description", ""),
                    "cert_type": data.get("cert_type", "general"),
                    "path": str(f),
                })
            except Exception as e:
                logger.warning(f"读取模板失败 [{f}]: {e}")
        return templates

    def load_template(self, name: str) -> Optional[dict]:
        """
        加载指定模板
        Args:
            name: 模板名称(不含扩展名)
        Returns:
            模板字典
        """
        if name in self._cache:
            return deepcopy(self._cache[name])

        path = self.template_dir / f"{name}.yaml"
        if not path.exists():
            logger.warning(f"模板不存在: {name}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._cache[name] = data
            logger.info(f"模板加载成功: {name}")
            return deepcopy(data)
        except Exception as e:
            logger.error(f"模板加载失败 [{name}]: {e}")
            return None

    def save_template(self, name: str, config: dict) -> bool:
        """
        保存模板到YAML文件
        Args:
            name: 模板名称
            config: 模板配置字典
        Returns:
            是否保存成功
        """
        path = self.template_dir / f"{name}.yaml"
        try:
            config["name"] = name
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            self._cache[name] = deepcopy(config)
            logger.info(f"模板保存成功: {path}")
            return True
        except Exception as e:
            logger.error(f"模板保存失败 [{name}]: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """删除模板"""
        path = self.template_dir / f"{name}.yaml"
        try:
            if path.exists():
                path.unlink()
            self._cache.pop(name, None)
            logger.info(f"模板已删除: {name}")
            return True
        except Exception as e:
            logger.error(f"模板删除失败 [{name}]: {e}")
            return False

    def create_default_template(self) -> dict:
        """创建默认模板副本"""
        return deepcopy(DEFAULT_TEMPLATE)

    def generate_from_keywords(self, name: str, cert_type: str,
                               keywords: List[str],
                               custom_patterns: Optional[Dict] = None) -> dict:
        """
        根据关键词自动生成模板
        Args:
            name: 模板名称
            cert_type: 证书类型
            keywords: 匹配关键词列表
            custom_patterns: 自定义字段正则
        Returns:
            生成的模板字典
        """
        template = self.create_default_template()
        template["name"] = name
        template["cert_type"] = cert_type
        template["keywords"] = keywords

        if custom_patterns:
            for field_name, patterns in custom_patterns.items():
                if field_name in template["fields"]:
                    if isinstance(patterns, list):
                        template["fields"][field_name]["patterns"] = patterns + \
                            template["fields"][field_name]["patterns"]
                    elif isinstance(patterns, dict):
                        template["fields"][field_name].update(patterns)

        return template

    def generate_interactive_template(self, name: str, cert_type: str,
                                      keywords: List[str],
                                      field_configs: Dict) -> dict:
        """
        交互式生成模板（由UI层调用，传入用户配置的字段信息）
        Args:
            name: 模板名称
            cert_type: 证书类型
            keywords: 关键词
            field_configs: 用户配置的字段信息
                {field_name: {patterns: [...], region: {x,y,w,h}, ...}}
        Returns:
            生成的模板字典
        """
        template = self.create_default_template()
        template["name"] = name
        template["cert_type"] = cert_type
        template["keywords"] = keywords
        template["description"] = f"交互式创建的{cert_type}类型模板"

        for field_name, config in field_configs.items():
            if field_name in template["fields"]:
                if "patterns" in config and config["patterns"]:
                    template["fields"][field_name]["patterns"] = config["patterns"]
                if "region" in config and config["region"]:
                    template["fields"][field_name]["region"] = config["region"]
                for key in ("separator", "location_hint", "name_hint"):
                    if key in config:
                        template["fields"][field_name][key] = config[key]
            else:
                template["fields"][field_name] = config

        return template

    def match_template(self, ocr_texts: List[str]) -> Optional[dict]:
        """
        根据OCR文本自动匹配最佳模板
        Args:
            ocr_texts: OCR识别的文本列表
        Returns:
            匹配到的模板，未匹配返回None
        """
        full_text = " ".join(ocr_texts).lower()
        best_match = None
        best_score = 0

        for tpl_info in self.list_templates():
            tpl = self.load_template(Path(tpl_info["path"]).stem)
            if not tpl:
                continue

            score = 0
            keywords = tpl.get("keywords", [])
            for kw in keywords:
                if kw.lower() in full_text:
                    score += 1

            if keywords and score > best_score:
                best_score = score
                best_match = tpl

        if best_match:
            match_rate = best_score / len(best_match.get("keywords", [1]))
            logger.info(f"模板匹配: {best_match['name']}，匹配率: {match_rate:.1%}")
            if match_rate >= 0.3:
                return best_match

        logger.info("未匹配到特定模板，使用默认模板")
        return self.create_default_template()
