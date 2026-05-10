from fastapi import APIRouter, BackgroundTasks

from app.services.storage import StorageService
from app.services.merger import MergerService

router = APIRouter()


@router.post("/")
async def merge_graphs(background_tasks: BackgroundTasks):
    if len(StorageService.graphs) < 2:
        return {"error": "Need at least 2 books to merge"}

    background_tasks.add_task(MergerService.merge_all)
    return {"message": "Merge started"}


@router.get("/decisions")
async def get_decisions():
    return {"decisions": StorageService.merge_decisions}


@router.get("/result")
async def get_merge_result():
    return StorageService.merge_result or {"error": "No merge result"}
