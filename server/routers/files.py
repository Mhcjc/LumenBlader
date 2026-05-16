from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/{folder_name}")
async def list_files(folder_name: str, request: Request):
    fm = request.app.state.file_manager
    return {
        "videos": fm.list_videos(folder_name),
        "analysis": fm.list_analysis(folder_name),
    }


@router.get("/{folder_name}/analysis/{filename}")
async def get_analysis_file(folder_name: str, filename: str, request: Request):
    fm = request.app.state.file_manager
    content = fm.get_analysis_content(folder_name, filename)
    if content is None:
        raise HTTPException(404, "分析文件不存在")
    return {"content": content, "filename": filename}
