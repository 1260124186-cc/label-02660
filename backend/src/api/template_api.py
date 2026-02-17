"""
模板管理 API
"""
import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)
router = APIRouter()

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "templates"
)
_template_mgr: Optional[TemplateManager] = None


def get_template_mgr() -> TemplateManager:
    global _template_mgr
    if _template_mgr is None:
        _template_mgr = TemplateManager(TEMPLATE_DIR)
    return _template_mgr


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    cert_type: str = "general"
    description: str = ""
    keywords: list[str] = []
    yaml_content: Optional[str] = None


class InteractiveFieldConfig(BaseModel):
    patterns: list[str] = []
    region: Optional[dict] = None
    separator: Optional[str] = None


class InteractiveTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    cert_type: str = "general"
    keywords: list[str] = []
    field_configs: dict[str, InteractiveFieldConfig] = {}


@router.get("/list")
async def list_templates():
    """获取所有模板列表"""
    mgr = get_template_mgr()
    templates = mgr.list_templates()
    result = []
    for tpl in templates:
        loaded = mgr.load_template(Path(tpl["path"]).stem)
        result.append({
            "name": tpl["name"],
            "cert_type": tpl["cert_type"],
            "description": tpl["description"],
            "keywords": loaded.get("keywords", []) if loaded else [],
        })
    return {"templates": result}


@router.get("/detail/{name}")
async def get_template(name: str):
    """获取模板详情"""
    mgr = get_template_mgr()
    tpl = mgr.load_template(name)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"模板不存在: {name}")
    return {"template": tpl}


@router.post("/create")
async def create_template(req: TemplateCreateRequest):
    """创建/更新模板"""
    mgr = get_template_mgr()

    if req.yaml_content:
        import yaml
        try:
            config = yaml.safe_load(req.yaml_content)
            if not isinstance(config, dict):
                raise ValueError("YAML内容必须是字典格式")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"YAML解析错误: {e}")
    else:
        config = mgr.create_default_template()

    config["name"] = req.name
    config["cert_type"] = req.cert_type
    config["description"] = req.description
    config["keywords"] = req.keywords

    if mgr.save_template(req.name, config):
        logger.info(f"模板创建/更新: {req.name}")
        return {"message": "保存成功", "name": req.name}
    else:
        raise HTTPException(status_code=500, detail="模板保存失败")


@router.post("/create-interactive")
async def create_interactive_template(req: InteractiveTemplateRequest):
    """交互式创建模板"""
    mgr = get_template_mgr()

    field_configs = {}
    for field_name, config in req.field_configs.items():
        fc = {}
        if config.patterns:
            fc["patterns"] = config.patterns
        if config.region:
            fc["region"] = config.region
        if config.separator:
            fc["separator"] = config.separator
        if fc:
            field_configs[field_name] = fc

    template = mgr.generate_interactive_template(
        req.name, req.cert_type, req.keywords, field_configs
    )

    if mgr.save_template(req.name, template):
        logger.info(f"交互式模板创建: {req.name}")
        return {"message": "模板已生成并保存", "name": req.name}
    else:
        raise HTTPException(status_code=500, detail="模板保存失败")


@router.delete("/{name}")
async def delete_template(name: str):
    """删除模板"""
    mgr = get_template_mgr()
    if mgr.delete_template(name):
        logger.info(f"模板已删除: {name}")
        return {"message": "已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")
