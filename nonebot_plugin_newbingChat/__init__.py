from nonebot import on_command

from .utils import newbing

# 使用bing的响应器
on_command("bing", priority=55, block=True, handlers=[newbing.bing_handle])
on_command("重置bing", aliases={"重置会话", "bing重置", "会话重置"}, priority=10, block=True, handlers=[newbing.reserve_bing])

