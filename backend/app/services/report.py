import os
from app.services.storage import StorageService


class ReportService:
    @classmethod
    async def generate(cls):
        # TODO: 生成整合报告数据
        return {
            "overview": {},
            "decisions_summary": {},
            "graph_stats": {},
            "cases": [],
            "completeness": "",
        }

    @classmethod
    async def save_md(cls):
        report = await cls.generate()
        path = "report/整合报告.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 整合报告\n\nTODO\n")
        return path
