from pathlib import Path
from typing import Optional, Sequence

from nonebot import get_driver
from pydantic import BaseSettings


class Config(BaseSettings):
    bing_cookie_path: Path = Path("data/new_bing")
    bing_private: bool = False
    newbing_cd_time: int = 600
    bing_proxy: str = ""
    superusers: Optional[Sequence[str]] = []
    bing_style_type: str = "creative"

    class Config:
        extra = "ignore"


config = Config.parse_obj(get_driver().config)


if not config.bing_cookie_path.exists() or not config.bing_cookie_path.is_dir():
    config.bing_cookie_path.mkdir(0o755, parents=True, exist_ok=True)
