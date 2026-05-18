from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import AppConfig
from .database import Database
from .services.file_manager import FileManager
from .services.downloader import TikTokDownloaderClient
from .services.analyzer import ContentAnalyzer
from .routers import accounts, downloads, analysis, files, settings


def create_app(config: AppConfig, db: Database = None) -> FastAPI:
    base_dir = Path(__file__).parent.parent
    materials_root = Path(config.materials_root)
    if not materials_root.is_absolute():
        materials_root = (base_dir / materials_root).resolve()

    db_path = base_dir / "data.db"
    if db is None:
        db = Database(db_path)

    file_manager = FileManager(materials_root)
    downloader = TikTokDownloaderClient(config.tiktok_downloader.api_base_url)
    analyzer = ContentAnalyzer(
        api_key=config.ai.api_key,
        base_url=config.ai.base_url,
        model=config.ai.model,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await db.init()
        yield
        await db.close()

    app = FastAPI(title="LumenBlader", version="0.1.0", lifespan=lifespan)

    app.state.db = db
    app.state.config = config
    app.state.config_path = base_dir / "config.json"
    app.state.file_manager = file_manager
    app.state.downloader = downloader
    app.state.analyzer = analyzer

    app.include_router(accounts.router)
    app.include_router(downloads.router)
    app.include_router(analysis.router)
    app.include_router(files.router)
    app.include_router(settings.router)

    frontend_dir = base_dir / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

        @app.get("/")
        async def index():
            return FileResponse(str(frontend_dir / "index.html"))

        @app.get("/app")
        async def app_page():
            return FileResponse(str(frontend_dir / "app.html"))

    return app


if __name__ == "__main__":
    import uvicorn
    from .config import load_config

    base_dir = Path(__file__).parent.parent
    config = load_config(base_dir / "config.json")
    app = create_app(config)
    uvicorn.run(app, host=config.server.host, port=config.server.port)
