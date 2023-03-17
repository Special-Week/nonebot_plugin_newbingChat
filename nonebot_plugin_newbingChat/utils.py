import os
import re
import json
import random
import nonebot
from loguru import logger
from EdgeGPT import Chatbot
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageEvent


# 不存在创建文件夹
if not os.path.exists("data/new_bing"):
    os.makedirs("data/new_bing")


config = nonebot.get_driver().config            # 获取配置文件
CDTIME: int = getattr(config, "cdtime", 30*60)  # 重置会话的cd时间
NICKNAME: str = getattr(config, "bot_nickname", "Hinata")  # 机器人昵称


# 会话字典，用于存储会话
chat_dict: dict = {
    #     "user_id": {
    #         "Chatbot": bot,
    #         "model":  balanced or creative or precise
    #         "last_time": xxx
    #         "isRunning": True or False
    #      }
}


# 初始化cookies, 注意这个cookies是一个长这样的列表[ [{},{},{}], [{},{},{}] ]
cookies: list = []
try:
    # 获取data/new_bing/所有以cookie文件
    cookie_files = [file for file in os.listdir(
        "data/new_bing") if file.startswith("cookie")]
    for file in cookie_files:
        if file.endswith(".json"):  # 如果是json文件
            with open(f"data/new_bing/{file}", "r", encoding="utf-8") as f:
                cookies.append(json.load(f))    # 加载json文件到列表里面
    logger.success(f"cookies读取, 初始化成功, 共{len(cookies)}个cookies")   # 打印日志
except:
    logger.info("cookies读取, 初始化失败")  # 初始化失败



async def new_chat_(event: MessageEvent, matcher: Matcher, user_id: str, style: str = "creative") -> str:
    """重置会话"""
    currentTime = event.time    # 获取当前时间
    if user_id in chat_dict:    # 如果用户id在会话字典里面
        last_time = chat_dict[user_id]["last_time"] # 获取上一次的时间
        if (currentTime - last_time < CDTIME) and (event.get_user_id() not in config.superusers):    # 如果当前时间减去上一次时间小于CD时间, 直接返回
            await matcher.finish(f"非报错情况下每个会话需要{CDTIME}秒才能新建哦, 当前还需要{CDTIME - (currentTime - last_time)}秒")
    # 如果用户id不在会话字典里面, 或者当前时间减去上一次时间大于CD时间, 重置会话
    bot = Chatbot(cookies=random.choice(cookies))       # 随机选择一个cookies创建一个Chatbot
    chat_dict.update({user_id: {"Chatbot": bot, "model": style,
                     "last_time": currentTime, "isRunning": False}})    # 更新会话字典
    return f"重置会话成功, bot: {str(bot)}, model: {style}, last_time: {currentTime}, isRunning: False"


def swap_string_positions(input_string: str) -> str:
    """处理一下返回的字符串"""
    input_string = re.sub(r'\[\^(\d+)\^\]', '', input_string)  # 去除[^1^]这种格式
    regex = r"\[\d+\]:"                                        # 匹配[1]:这种格式
    matches = re.findall(regex, input_string)                  # 找到所有匹配的字符串
    if not matches:                                          # 如果没有匹配到
        # 直接替换
        return input_string.replace("bing", NICKNAME).replace("Bing", NICKNAME).replace("必应", NICKNAME)
    positions = [(match.start(), match.end())
                 for match in re.finditer(regex, input_string)]        # 找到所有匹配的位置
    # 找到最后一个匹配的位置的换行符
    end = input_string.find("\n", positions[len(positions)-1][1])
    target = (input_string[end:]).replace("bing", NICKNAME).replace(
        "Bing", NICKNAME).replace("必应", NICKNAME) + "\n\n" + input_string[:end]  # 替换
    while target[0] == "\n":    # 去除开头的换行符
        target = target[1:]
    return target   # 返回替换后的字符串


def hello() -> str:
    """随机问候语"""
    result = random.choice(
        (
            "哦豁？！",
            "你好！Ov<",
            f"库库库，呼唤Hinata做什么呢",
            "我在呢！",
            "呼呼，叫俺干嘛",
        )
    )
    return result


async def getUsage() -> str:
    return __usage__


__usage__ = f"""这是一个调用new bing的插件, 通过at机器人加内容触发, 默认会话为creative, 限制的会话重置时间为{CDTIME}秒, 会话重置时间可在.env中修改
手动重置会话: 重置会话 + 模式, 模式为balanced, creative, precise, 默认为creative
"""