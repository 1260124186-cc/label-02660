"""
证书识别 API
"""
import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from src.core.processor import CertProcessor
from src.core.excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "upload")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

_processor: Optional[CertProcessor] = None


def get_processor() -> CertProcessor:
    global _processor
    if _processor is None:
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "templates"
        )
        _processor = CertProcessor(template_dir=template_dir)
    return _processor


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """上传证书文件"""
    batch_id = str(uuid.uuid4())[:8]
    batch_dir = os.path.join(UPLOAD_DIR, batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    saved = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}:
            continue
        save_path = os.path.join(batch_dir, f.filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as fp:
            content = await f.read()
            fp.write(content)
        saved.append(f.filename)
        logger.info(f"文件上传: {f.filename} -> {batch_id}")

    if not saved:
        raise HTTPException(status_code=400, detail="没有有效的证书文件")

    return {"batch_id": batch_id, "files": saved, "count": len(saved)}


@router.post("/process")
async def process_batch(
    batch_id: str = Form(...),
    write_mode: str = Form("overwrite"),
    has_previous: str = Form("false"),
    output_filename: str = Form("result_all"),
    output_dir: str = Form(""),
):
    """处理已上传的证书批次"""
    batch_dir = os.path.join(UPLOAD_DIR, batch_id)
    if not os.path.isdir(batch_dir):
        raise HTTPException(status_code=404, detail=f"批次不存在: {batch_id}")

    # 安全处理文件名：去除路径分隔符，确保以 .xlsx 结尾
    safe_name = os.path.basename(output_filename.strip() or "result_all")
    if not safe_name.endswith(".xlsx"):
        safe_name = safe_name + ".xlsx"

    # 处理输出目录：清理路径，防止目录穿越
    sub_dir = output_dir.strip().strip("/\\")
    if sub_dir:
        # 防止 .. 路径穿越
        safe_parts = [p for p in sub_dir.replace("\\", "/").split("/") if p and p != ".."]
        sub_dir = os.path.join(*safe_parts) if safe_parts else ""

    if sub_dir:
        actual_output_dir = os.path.join(OUTPUT_DIR, sub_dir)
    else:
        actual_output_dir = OUTPUT_DIR
    os.makedirs(actual_output_dir, exist_ok=True)
    output_path = os.path.join(actual_output_dir, safe_name)

    # 用于返回和下载的相对路径
    relative_path = os.path.join(sub_dir, safe_name) if sub_dir else safe_name

    # 覆盖模式：先删除旧文件确保干净
    # 追加模式但前端无历史数据时（has_previous=false），也当覆盖处理
    actual_write_mode = write_mode
    if write_mode == "overwrite":
        if os.path.isfile(output_path):
            os.remove(output_path)
    elif write_mode == "append" and has_previous == "false":
        actual_write_mode = "overwrite"
        if os.path.isfile(output_path):
            os.remove(output_path)

    processor = get_processor()
    try:
        processor.init_engines()
        result = processor.process_folder(batch_dir, output_path, actual_write_mode)

        results_data = []
        for info in result.results:
            results_data.append(info.to_dict())

        # 追加模式下，从Excel读取全部数据返回给前端
        all_results_data = results_data
        if actual_write_mode == "append" and os.path.isfile(output_path):
            try:
                import pandas as pd
                import math
                df = pd.read_excel(output_path, engine="openpyxl")
                from src.core.excel_exporter import COLUMNS
                reverse_cols = {v: k for k, v in COLUMNS.items()}
                all_results_data = []
                for _, row in df.iterrows():
                    item = {}
                    for cn_name, en_name in reverse_cols.items():
                        val = row.get(cn_name, "")
                        # 处理 NaN/inf 等非法浮点值
                        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                            val = 0 if en_name == "confidence" else ""
                        elif pd.isna(val):
                            val = ""
                        item[en_name] = val
                    all_results_data.append(item)
            except Exception as e:
                logger.warning(f"读取合并数据失败: {e}")

        # 在追加模式下，使用实际返回的所有结果数量作为总统计
        if actual_write_mode == "append":
            total_count = len(all_results_data)
            success_count = total_count  # 所有保存到Excel的都是成功的
            return {
                "batch_id": batch_id,
                "total": total_count,
                "success": success_count,
                "failed": result.failed,
                "results": all_results_data,
                "errors": result.errors,
                "output_file": relative_path,
            }
        else:
            # 覆盖模式下使用本轮统计
            return {
                "batch_id": batch_id,
                "total": result.total,
                "success": result.success,
                "failed": result.failed,
                "results": all_results_data,
                "errors": result.errors,
                "output_file": relative_path,
            }
    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filepath:path}")
async def download_result(filepath: str):
    """下载识别结果Excel"""
    # 安全处理：防止路径穿越
    safe_path = os.path.normpath(filepath).lstrip(os.sep)
    if ".." in safe_path.split(os.sep):
        raise HTTPException(status_code=400, detail="非法路径")
    file_path = os.path.join(OUTPUT_DIR, safe_path)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(safe_path),
    )


@router.post("/recognize-single")
async def recognize_single(file: UploadFile = File(...)):
    """单文件识别（不保存Excel）"""
    ext = Path(file.filename).suffix.lower()
    if ext not in {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    tmp_dir = os.path.join(UPLOAD_DIR, f"tmp_{uuid.uuid4().hex[:6]}")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, file.filename)

    try:
        with open(tmp_path, "wb") as fp:
            fp.write(await file.read())

        processor = get_processor()
        processor.init_engines()
        cert_info = processor.process_single(tmp_path)

        if cert_info:
            return {"success": True, "data": cert_info.to_dict()}
        else:
            return {"success": False, "data": None, "message": "未能识别证书信息"}
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.delete("/batch/{batch_id}")
async def delete_batch(batch_id: str):
    """删除上传批次"""
    batch_dir = os.path.join(UPLOAD_DIR, batch_id)
    if os.path.isdir(batch_dir):
        shutil.rmtree(batch_dir, ignore_errors=True)
    output_file = os.path.join(OUTPUT_DIR, f"result_{batch_id}.xlsx")
    if os.path.isfile(output_file):
        os.remove(output_file)
    logger.info(f"批次已删除: {batch_id}")
    return {"message": "已删除"}
