from fastapi import APIRouter

from app.services.report import ReportService

router = APIRouter()


@router.post("/generate")
async def generate_report():
    report = await ReportService.generate()
    # 自动保存 MD 文件到磁盘
    await ReportService.save_md()
    return {"success": True, "report": report}


@router.get("/download")
async def download_report():
    path = await ReportService.save_md()
    return {"path": path}
