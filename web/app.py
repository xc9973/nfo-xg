"""NFO Editor Web Version - FastAPI Backend."""
import os
import sys
import secrets
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.background import BackgroundTasks
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nfo_editor.models.nfo_model import NfoData, Actor
from nfo_editor.models.nfo_types import NfoType
from nfo_editor.models.template import NfoTemplate, TemplateManager
from nfo_editor.utils.xml_parser import XmlParser
from nfo_editor.utils.validation import validate_nfo_data
from nfo_editor.utils.exceptions import ParseError, FileError
from nfo_editor.batch import (
    TaskManager,
    TaskStatus,
    BatchTask,
    BatchPreviewRequest,
    BatchApplyRequest,
    BatchPreviewResponse,
    BatchStatusResponse,
)
from nfo_editor.batch.processor import BatchProcessor

from nfo_editor.services.tmdb_client import TMDBClient
from nfo_editor.services.tmdb_mapper import TMDBMapper

app = FastAPI(title="NFO Editor", version="1.0.0")

# 密码认证 (从环境变量读取，默认无密码)
NFO_PASSWORD = os.environ.get("NFO_PASSWORD", "")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
security = HTTPBasic()

# 模板管理器
template_mgr = TemplateManager(Path(__file__).parent / "templates.json")

# TMDB 客户端和映射器
tmdb_client = TMDBClient(api_key=TMDB_API_KEY)
tmdb_mapper = TMDBMapper(tmdb_client=tmdb_client)


def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """验证密码（如果设置了的话）"""
    if not NFO_PASSWORD:
        return True  # 未设置密码，跳过验证
    
    if not secrets.compare_digest(credentials.password, NFO_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# Setup templates and static files
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

parser = XmlParser()
batch_processor = BatchProcessor(parser)


# Pydantic models for API
class ActorModel(BaseModel):
    name: str
    role: str = ""
    thumb: str = ""
    order: int = 0


class NfoDataModel(BaseModel):
    nfo_type: str = "movie"
    title: str = ""
    originaltitle: str = ""
    year: str = ""
    plot: str = ""
    runtime: str = ""
    genres: List[str] = []
    directors: List[str] = []
    actors: List[ActorModel] = []
    studio: str = ""
    rating: str = ""
    poster: str = ""
    fanart: str = ""
    season: str = ""
    episode: str = ""
    aired: str = ""


class FileRequest(BaseModel):
    path: str


class SaveRequest(BaseModel):
    path: str
    data: NfoDataModel


class ListDirRequest(BaseModel):
    path: str = ""


class TemplateModel(BaseModel):
    name: str
    nfo_type: str = "movie"
    genres: List[str] = []
    directors: List[str] = []
    studio: str = ""


# ========== 搜索模型 ==========

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str           # 搜索关键词
    path: str = ""       # 搜索起始目录，默认为用户主目录
    max_depth: int = 5   # 最大递归深度
    max_results: int = 50  # 最大结果数


class SearchResultItem(BaseModel):
    """搜索结果项模型"""
    path: str            # 文件完整路径
    filename: str        # 文件名
    match_type: str      # 匹配类型: "filename" | "title" | "originaltitle" | "actor" | "plot"
    match_field: str     # 匹配的具体字段值
    title: str = ""      # NFO 标题（如果有）


# ========== TMDB 模型 ==========

class TmdbSearchRequest(BaseModel):
    """TMDB 搜索请求模型"""
    query: str
    page: int = 1


class TmdbConfigRequest(BaseModel):
    """TMDB 配置请求模型"""
    api_key: str


# ========== 搜索核心逻辑 ==========

def scan_nfo_files(base_path: Path, max_depth: int, current_depth: int = 0) -> List[Path]:
    """递归扫描目录查找 NFO 文件
    
    Args:
        base_path: 起始目录
        max_depth: 最大递归深度
        current_depth: 当前深度
        
    Returns:
        NFO 文件路径列表
    """
    nfo_files = []
    
    if current_depth > max_depth:
        return nfo_files
    
    try:
        for item in base_path.iterdir():
            if item.name.startswith('.'):
                continue
            if item.is_file() and item.suffix.lower() == '.nfo':
                nfo_files.append(item)
            elif item.is_dir():
                nfo_files.extend(scan_nfo_files(item, max_depth, current_depth + 1))
    except PermissionError:
        # 跳过无权限访问的目录
        pass
    
    return nfo_files


def match_filename(filename: str, query: str) -> bool:
    """检查文件名是否匹配查询（大小写不敏感）
    
    Args:
        filename: 文件名
        query: 搜索关键词
        
    Returns:
        是否匹配
    """
    return query.lower() in filename.lower()


def match_nfo_content(file_path: Path, query: str, xml_parser: XmlParser) -> Optional[tuple]:
    """检查 NFO 内容是否匹配查询
    
    Args:
        file_path: NFO 文件路径
        query: 搜索关键词
        xml_parser: XML 解析器
        
    Returns:
        匹配结果元组 (match_type, match_field, title) 或 None
    """
    try:
        data = xml_parser.parse(str(file_path))
        query_lower = query.lower()
        
        # 检查 title
        if data.title and query_lower in data.title.lower():
            return ("title", data.title, data.title)
        
        # 检查 originaltitle
        if data.originaltitle and query_lower in data.originaltitle.lower():
            return ("originaltitle", data.originaltitle, data.title)
        
        # 检查 actors
        for actor in data.actors:
            if actor.name and query_lower in actor.name.lower():
                return ("actor", actor.name, data.title)
        
        # 检查 plot
        if data.plot and query_lower in data.plot.lower():
            return ("plot", data.plot[:100] + "..." if len(data.plot) > 100 else data.plot, data.title)
        
        return None
    except (ParseError, FileError, Exception):
        # 解析失败，跳过内容匹配
        return None


def search_nfo_files(
    query: str,
    base_path: Path,
    max_depth: int,
    max_results: int,
    xml_parser: XmlParser
) -> tuple:
    """搜索 NFO 文件
    
    Args:
        query: 搜索关键词
        base_path: 搜索起始目录
        max_depth: 最大递归深度
        max_results: 最大结果数
        xml_parser: XML 解析器
        
    Returns:
        (结果列表, 是否截断)
    """
    if not query.strip():
        return [], False
    
    results = []
    seen_paths = set()  # 用于去重
    
    # 扫描所有 NFO 文件
    nfo_files = scan_nfo_files(base_path, max_depth)
    
    for file_path in nfo_files:
        if len(results) >= max_results:
            return results, True  # 已达到最大结果数，标记截断
        
        path_str = str(file_path)
        if path_str in seen_paths:
            continue
        
        # 先检查文件名匹配
        if match_filename(file_path.name, query):
            seen_paths.add(path_str)
            # 尝试获取标题
            title = ""
            try:
                data = xml_parser.parse(path_str)
                title = data.title
            except:
                pass
            results.append(SearchResultItem(
                path=path_str,
                filename=file_path.name,
                match_type="filename",
                match_field=file_path.name,
                title=title
            ))
            continue
        
        # 检查内容匹配
        content_match = match_nfo_content(file_path, query, xml_parser)
        if content_match:
            seen_paths.add(path_str)
            match_type, match_field, title = content_match
            results.append(SearchResultItem(
                path=path_str,
                filename=file_path.name,
                match_type=match_type,
                match_field=match_field,
                title=title or ""
            ))
    
    return results, False


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, auth: bool = Depends(check_auth)):
    """Render main page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/list")
async def list_directory(req: ListDirRequest, auth: bool = Depends(check_auth)):
    """List NFO files in directory."""
    base_path = req.path or os.path.expanduser("~")
    path = Path(base_path)
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="目录不存在")
    
    if not path.is_dir():
        raise HTTPException(status_code=400, detail="不是目录")
    
    items = []
    try:
        for item in sorted(path.iterdir()):
            if item.name.startswith('.'):
                continue
            # 只显示目录和 .nfo 文件
            if item.is_dir() or item.suffix.lower() == ".nfo":
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "is_nfo": item.suffix.lower() == ".nfo"
                })
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限访问")
    
    return {
        "current": str(path),
        "parent": str(path.parent) if path.parent != path else None,
        "items": items
    }


@app.post("/api/load")
async def load_nfo(req: FileRequest, auth: bool = Depends(check_auth)):
    """Load and parse NFO file."""
    try:
        data = parser.parse(req.path)
        return {
            "success": True,
            "data": {
                "nfo_type": data.nfo_type.value,
                "title": data.title,
                "originaltitle": data.originaltitle,
                "year": data.year,
                "plot": data.plot,
                "runtime": data.runtime,
                "genres": data.genres,
                "directors": data.directors,
                "actors": [asdict(a) for a in data.actors],
                "studio": data.studio,
                "rating": data.rating,
                "poster": data.poster,
                "fanart": data.fanart,
                "season": data.season,
                "episode": data.episode,
                "aired": data.aired,
            }
        }
    except FileError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ParseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/save")
async def save_nfo(req: SaveRequest, auth: bool = Depends(check_auth)):
    """Save NFO file."""
    try:
        nfo_type = NfoType(req.data.nfo_type)
    except ValueError:
        nfo_type = NfoType.MOVIE
    
    actors = [Actor(**a.model_dump()) for a in req.data.actors]
    
    data = NfoData(
        nfo_type=nfo_type,
        title=req.data.title,
        originaltitle=req.data.originaltitle,
        year=req.data.year,
        plot=req.data.plot,
        runtime=req.data.runtime,
        genres=req.data.genres,
        directors=req.data.directors,
        actors=actors,
        studio=req.data.studio,
        rating=req.data.rating,
        poster=req.data.poster,
        fanart=req.data.fanart,
        season=req.data.season,
        episode=req.data.episode,
        aired=req.data.aired,
    )
    
    # Validate
    is_valid, errors = validate_nfo_data(data)
    if not is_valid:
        error_msgs = [e.message for e in errors]
        raise HTTPException(status_code=400, detail="; ".join(error_msgs))
    
    try:
        parser.save(data, req.path)
        return {"success": True, "message": "保存成功"}
    except FileError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validate")
async def validate_data(data: NfoDataModel, auth: bool = Depends(check_auth)):
    """Validate NFO data without saving."""
    try:
        nfo_type = NfoType(data.nfo_type)
    except ValueError:
        nfo_type = NfoType.MOVIE
    
    actors = [Actor(**a.model_dump()) for a in data.actors]
    
    nfo_data = NfoData(
        nfo_type=nfo_type,
        title=data.title,
        year=data.year,
        rating=data.rating,
        runtime=data.runtime,
        genres=data.genres,
        directors=data.directors,
        actors=actors,
    )
    
    is_valid, errors = validate_nfo_data(nfo_data)
    return {
        "is_valid": is_valid,
        "errors": [{"field": e.field, "message": e.message} for e in errors]
    }


# ========== 模板 API ==========

@app.get("/api/templates")
async def list_templates(auth: bool = Depends(check_auth)):
    """列出所有模板"""
    return {"templates": [t.to_dict() for t in template_mgr.list_all()]}


@app.post("/api/templates")
async def save_template(template: TemplateModel, auth: bool = Depends(check_auth)):
    """保存模板"""
    t = NfoTemplate(
        name=template.name,
        nfo_type=template.nfo_type,
        genres=template.genres,
        directors=template.directors,
        studio=template.studio,
    )
    template_mgr.add(t)
    return {"success": True, "message": "模板已保存"}


@app.delete("/api/templates/{name}")
async def delete_template(name: str, auth: bool = Depends(check_auth)):
    """删除模板"""
    if template_mgr.delete(name):
        return {"success": True, "message": "模板已删除"}
    raise HTTPException(status_code=404, detail="模板不存在")


@app.get("/api/templates/{name}")
async def get_template(name: str, auth: bool = Depends(check_auth)):
    """获取单个模板"""
    t = template_mgr.get(name)
    if t:
        return {"template": t.to_dict()}
    raise HTTPException(status_code=404, detail="模板不存在")


# ========== 搜索 API ==========

@app.post("/api/search")
async def search(req: SearchRequest, auth: bool = Depends(check_auth)):
    """搜索 NFO 文件
    
    支持按文件名和内容（title, originaltitle, actors, plot）搜索
    """
    # 确定搜索起始目录
    base_path = req.path or os.path.expanduser("~")
    path = Path(base_path)
    
    # 验证目录
    if not path.exists():
        raise HTTPException(status_code=404, detail="目录不存在")
    
    if not path.is_dir():
        raise HTTPException(status_code=400, detail="不是目录")
    
    try:
        results, truncated = search_nfo_files(
            query=req.query,
            base_path=path,
            max_depth=req.max_depth,
            max_results=req.max_results,
            xml_parser=parser
        )
        
        return {
            "results": [r.model_dump() for r in results],
            "truncated": truncated
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限访问")


# ========== 批量编辑 API ==========

@app.post("/api/batch/preview", response_model=BatchPreviewResponse)
async def batch_preview(
    req: BatchPreviewRequest,
    auth: bool = Depends(check_auth)
):
    """预览批量修改操作

    返回:
    - task_id: 用于后续执行
    - total_files: 将被修改的文件数
    - sample_files: 前5个文件预览（显示当前值和新值）
    """
    path = Path(req.directory)
    if not path.exists():
        raise HTTPException(status_code=404, detail="目录不存在")

    if not path.is_dir():
        raise HTTPException(status_code=400, detail="不是目录")

    # 执行预览
    try:
        files = batch_processor.preview(
            directory=str(path),
            field=req.field,
            value=req.value,
            mode=req.mode
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=413, detail=str(e))

    # 创建预览任务
    task = BatchTask(
        task_id=str(uuid.uuid4()),
        status=TaskStatus.PENDING,
        total_files=len(files),
        processed_files=0,
        success_count=0,
        failed_count=0,
        errors=[],
        created_at=datetime.now(),
        field=req.field,
        value=req.value,
        mode=req.mode,
        directory=req.directory,
        preview_files=files
    )

    # 保存任务到管理器
    task_manager = TaskManager()
    task_manager.add(task)

    # 返回前5个文件作为样本
    sample_files = files[:5] if len(files) > 5 else files

    return BatchPreviewResponse(
        task_id=task.task_id,
        total_files=len(files),
        sample_files=sample_files
    )


@app.post("/api/batch/apply")
async def batch_apply(
    req: BatchApplyRequest,
    background_tasks: BackgroundTasks,
    auth: bool = Depends(check_auth)
):
    """执行批量修改（后台任务）"""
    task_manager = TaskManager()
    task = task_manager.get(req.task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not req.confirmed:
        raise HTTPException(status_code=400, detail="需要确认才能执行")

    # 定义后台任务函数
    def run_batch_task():
        try:
            batch_processor.apply(
                task_id=req.task_id,
                files=task.preview_files,
                field=task.field,
                value=task.value,
                mode=task.mode
            )
        except Exception as e:
            # 更新任务状态为失败
            task.status = TaskStatus.FAILED
            task.errors.append(f"执行失败: {str(e)}")

    # 添加到后台任务队列
    background_tasks.add_task(run_batch_task)

    return {
        "task_id": req.task_id,
        "status": "running",
        "message": "批量修改任务已启动"
    }


@app.get("/api/batch/status/{task_id}", response_model=BatchStatusResponse)
async def batch_status(
    task_id: str,
    auth: bool = Depends(check_auth)
):
    """查询任务进度"""
    task_manager = TaskManager()
    task = task_manager.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return BatchStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        progress=task.progress,
        processed=task.processed_files,
        total=task.total_files,
        success=task.success_count,
        failed=task.failed_count,
        errors=task.errors[-10:]  # 返回最近10条错误
    )


# ========== TMDB API ==========

@app.get("/api/tmdb/search")
async def tmdb_search(query: str, page: int = 1, auth: bool = Depends(check_auth)):
    """搜索 TMDB 电影和电视剧"""
    try:
        raw_data = tmdb_client.search_multi(query, page)

        # Transform results to match frontend expectations
        transformed_results = []
        for item in raw_data.get("results", []):
            # Extract year from date
            date_str = item.get("release_date") or item.get("first_air_date", "")
            year = date_str.split("-")[0] if date_str else ""

            # Get poster URL
            poster_url = tmdb_client.get_image_url(item.get("poster_path"))

            # Get title (handle both movie and TV)
            title = item.get("title") or item.get("name", "")

            transformed_results.append({
                "id": item["id"],
                "media_type": item["media_type"],
                "title": title,
                "year": year,
                "poster_url": poster_url
            })

        return {
            "page": raw_data.get("page", page),
            "total_pages": raw_data.get("total_pages", 0),
            "total_results": raw_data.get("total_results", 0),
            "results": transformed_results,
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tmdb/movie/{tmdb_id}")
async def tmdb_get_movie(tmdb_id: int, auth: bool = Depends(check_auth)):
    """获取 TMDB 电影详情"""
    try:
        data = tmdb_client.get_movie_details(tmdb_id)
        nfo_data = tmdb_mapper.map_movie(data)
        return asdict(nfo_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tmdb/tv/{tmdb_id}")
async def tmdb_get_tv(tmdb_id: int, auth: bool = Depends(check_auth)):
    """获取 TMDB 电视剧详情"""
    try:
        data = tmdb_client.get_tv_details(tmdb_id)
        nfo_data = tmdb_mapper.map_tv_show(data)
        return asdict(nfo_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tmdb/tv/{tmdb_id}/season/{season}/episode/{episode}")
async def tmdb_get_episode(
    tmdb_id: int, season: int, episode: int, auth: bool = Depends(check_auth)
):
    """获取 TMDB 单集详情"""
    try:
        data = tmdb_client.get_tv_episode_details(tmdb_id, season, episode)
        nfo_data = tmdb_mapper.map_episode(data)
        return asdict(nfo_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tmdb/config")
async def tmdb_config(req: TmdbConfigRequest, auth: bool = Depends(check_auth)):
    """配置 TMDB API Key"""
    # 这里简单地更新当前实例的 API Key
    # 在实际生产环境中，应该将 API Key 持久化存储（例如写入配置文件或数据库）
    tmdb_client.api_key = req.api_key
    return {"success": True, "message": "TMDB API Key 已更新"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1111)
