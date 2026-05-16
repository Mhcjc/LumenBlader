import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server.main import create_app
from server.config import load_config
import uvicorn


def main():
    config_path = Path(__file__).parent / "config.json"
    config = load_config(config_path)
    app = create_app(config)
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
    )


if __name__ == "__main__":
    main()
