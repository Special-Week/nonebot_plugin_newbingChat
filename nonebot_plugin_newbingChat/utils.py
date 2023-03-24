import json
import os
import random
import re

from EdgeGPT import Chatbot
from loguru import logger
from nonebot.adapters.onebot.v11 import (Message, MessageEvent, MessageSegment,
                                         PrivateMessageEvent)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from .config import config
from .txt_to_img import txt_to_img


class NewBing:
    def __init__(self) -> None:
        """初始化newbing, 标记cookie是否有效, 以及是否私聊启用"""
        self.__usage__ = f"这是一个调用new bing的插件, 通过使用bing命令头触发, 默认会话为creative(.env可修改), 限制的会话重置时间为{config.newbing_cd_time}秒"
        self.hello_reply: tuple = (
            "你好！",
            "哦豁？！",
            "你好！Ov<",
            "库库库，呼唤咱做什么呢",
            "我在呢！",
            "呼呼，叫俺干嘛",
        )
        self.nonsense: tuple = (
            "你好啊",
            "你好",
            "在吗",
            "在不在",
            "您好",
            "您好啊",
            "你好",
            "在",
        )
        self.bing_chat_dict: dict = {}
        bing_cookies_files: list = [
            file
            for file in config.bing_cookie_path.rglob("*.json")
            if file.stem.startswith("cookie")
        ]
        try:
            self.bing_cookies: list = [
                json.load(open(file, "r", encoding="utf-8")) for file in bing_cookies_files
            ]
            logger.success(f"bing_cookies读取, 初始化成功, 共{len(self.bing_cookies)}个cookies")
        except Exception as e:
            logger.error(f"读取bing cookies失败 error信息: {str(e)}")
            self.bing_cookies: list = []
        if config.bing_proxy:
            os.environ["all_proxy"] = config.bing_proxy
            logger.info(f"已设置代理, 值为:{config.bing_proxy}")
        else:
            logger.warning("未检测到代理，国内用户可能无法使用bing或openai功能")


    async def newbing_new_chat(self, event: MessageEvent, matcher: Matcher) -> None:
        """重置会话"""
        current_time: int = event.time
        user_id: str = str(event.user_id)
        if user_id in self.bing_chat_dict:
            last_time: int = self.bing_chat_dict[user_id]["last_time"]
            if (current_time - last_time < config.newbing_cd_time) and (
                event.get_user_id() not in config.superusers
            ):  # 如果当前时间减去上一次时间小于CD时间, 直接返回
                await matcher.finish(
                    f"非报错情况下每个会话需要{config.newbing_cd_time}秒才能新建哦, 当前还需要{config.newbing_cd_time - (current_time - last_time)}秒"
                )
        bot = Chatbot(cookies=random.choice(self.bing_cookies))  # 随机选择一个cookies创建一个Chatbot
        self.bing_chat_dict[user_id] = {"chatbot": bot, "last_time": current_time, "model": config.bing_style_type, "isRunning": False}


    async def bing_string_handle(self, input_string: str) -> str:
        """处理一下bing返回的字符串"""
        input_string = re.sub(r"\[\^(\d+)\^\]", "", input_string)
        regex = r"\[\d+\]:"
        matches = re.findall(regex, input_string)
        if not matches:
            return input_string
        positions = [
            (match.start(), match.end()) for match in re.finditer(regex, input_string)
        ]
        end = input_string.find("\n", positions[-1][1])
        target = input_string[end:] + "\n\n" + input_string[:end]
        while target[0] == "\n":
            target = target[1:]
        return target
    


    async def reserve_bing(
        self,
        matcher: Matcher, 
        event: MessageEvent
    ) -> None:
        await self.newbing_new_chat(event=event, matcher=matcher)
        await matcher.send("newbing会话已重置", at_sender=True)


    async def pretreatment(
        self, 
        event: MessageEvent,
        matcher: Matcher, 
        msg: str
    ):  
        """稍微预处理一下"""
        uid = event.get_user_id()  # 获取用户id
        if not config.bing_private and isinstance(event, PrivateMessageEvent):
            await matcher.finish()          # 配置私聊不启用后，私聊信息直接结束处理
        if msg.isspace() or not msg:        # 如果消息为空或者全为空格, 则结束处理
            await matcher.finish()
        if not self.bing_cookies:
            await matcher.finish("cookie未设置, 无法访问")
        if msg in self.nonsense:
            await matcher.finish(random.choice(self.hello_reply))
        if uid not in self.bing_chat_dict:
            await self.newbing_new_chat(event=event, matcher=matcher)
            await matcher.send("newbing新会话已创建", at_sender=True)
        if self.bing_chat_dict[uid]["isRunning"]:
            await matcher.finish("当前会话正在运行中, 请稍后再发起请求", at_sender=True)
        self.bing_chat_dict[uid]["isRunning"] = True

        
    async def bing_handle(
        self,
        matcher: Matcher, 
        event: MessageEvent, 
        args: Message = CommandArg()
    ): 
        """newbing聊天的handle函数"""
        uid = event.get_user_id()  # 获取用户id
        msg = args.extract_plain_text()  # 获取消息
        
        await self.pretreatment(event=event, matcher=matcher, msg=msg)      # 预处理

        bot: Chatbot = self.bing_chat_dict[uid]["chatbot"]  # 获取当前会话的Chatbot对象
        style: str = self.bing_chat_dict[uid]["model"]  # 获取当前会话的对话样式
        try:  # 尝试获取bing的回复
            data = await bot.ask(prompt=msg, conversation_style=style)
        except Exception as e:  # 如果出现异常, 则返回异常信息, 并且将当前会话状态设置为未运行
            self.bing_chat_dict[uid]["isRunning"] = False
            await matcher.finish(f'askError: {str(e)}多次askError请尝试"重置bing"', at_sender=True)
        self.bing_chat_dict[uid]["isRunning"] = False  # 将当前会话状态设置为未运行
        if (
            data["item"]["result"]["value"] != "Success"
        ):  # 如果返回的结果不是Success, 则返回错误信息, 并且删除当前会话
            await matcher.send(
                "返回Error: " + data["item"]["result"]["value"] + "请重试", at_sender=True
            )
            del self.bing_chat_dict[uid]
            return

        throttling = data["item"]["throttling"]  # 获取当前会话的限制信息
        # 获取当前会话的最大对话数
        max_conversation = throttling["maxNumUserMessagesInConversation"]
        # 获取当前会话的当前对话数
        current_conversation = throttling["numUserMessagesInConversation"]
        if len(data["item"]["messages"]) < 2:  # 如果返回的消息数量小于2, 则说明会话已经中断, 则删除当前会话
            await matcher.send("该对话已中断, 可能是被bing掐了, 正帮你重新创建会话", at_sender=True)
            await self.newbing_new_chat(event=event, matcher=matcher)
            return
        # 如果返回的消息中没有text, 则说明提问了敏感问题, 则删除当前会话
        if "text" not in data["item"]["messages"][1]:
            await matcher.send(
                data["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"],
                at_sender=True,
            )
            return
        rep_message = await self.bing_string_handle(
            data["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]
        )  # 获取bing的回复, 并且稍微处理一下
        try:  # 尝试发送回复
            await matcher.send(
                f"{rep_message}\n\n当前{current_conversation} 共 {max_conversation}",
                at_sender=True,
            )
            if max_conversation <= current_conversation:
                await matcher.send("达到对话上限, 正帮你重置会话", at_sender=True)
                try:
                    await self.newbing_new_chat(event=event, matcher=matcher)
                except Exception:
                    return
        except Exception as e:  # 如果发送失败, 则尝试把文字写在图片上发送
            try:
                await matcher.send(
                    f"文本消息可能被风控了\n错误信息:{str(e)}\n这里咱尝试把文字写在图片上发送了{MessageSegment.image(await self.text_to_img(rep_message))}",
                    at_sender=True,
                )
            except Exception as eeee:  # 如果还是失败, 我也没辙了, 只能返回异常信息了
                await matcher.send(f"消息全被风控了, 这是捕获的异常: \n{str(eeee)}", at_sender=True)


    async def text_to_img(self, text: str) -> bytes:
        """将文字转换为图片"""
        return await txt_to_img.txt_to_img(text)
    
    async def get_usage(self) -> str:
        return self.__usage__

# 实例化一个NewBing对象
newbing = NewBing()





