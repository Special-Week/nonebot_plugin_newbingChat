from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .utils import *
from .txt_to_img import txt_to_png

bingchat = on_message(rule=to_me(), priority=1145141919810, block=False)
reserve = on_command("重置会话", aliases={"重置bing"}, priority=10, block=True)
bingHelp = on_command("bing帮助", aliases={"binghelp"}, priority=10, block=True)


@bingchat.handle()
async def _(mathcer: Matcher, event: MessageEvent):
    uid = event.get_user_id()               # 获取用户id
    msg = str(event.get_message())          # 获取用户消息
    msg = re.sub(r"\[.*?\]", "", msg)       # 去除消息中的带cq码的部分, 即保留纯文本消息
    if cookies == []:                       # 如果cookies为空, 则无法访问bing
        await bingchat.finish("cookie未设置, 无法访问")
    if (msg.isspace() or msg == "" or msg in [
        "你好啊",
        "你好",
        "在吗",
        "在不在",
        "您好",
        "您好啊",
        "你好",
        "在",
    ]):                                     # 如果消息为空或者是一些无意义的问候, 则返回一些问候语
        await bingchat.finish(hello())
    if uid not in chat_dict:                # 如果用户id不在会话字典中, 则新建一个会话
        _ = await new_chat_(event=event, matcher=mathcer, user_id=uid)
        await bingchat.send("新会话已创建, 当前模式creative, 如要切换对话样式请发送“重置会话”， 并附带参数 balanced 或者 creative 或 precise", at_sender=True)
    if chat_dict[uid]["isRunning"]:             # 如果当前会话正在运行, 则返回正在运行
        await bingchat.finish("当前会话正在运行中, 请稍等", at_sender=True)
    chat_dict[uid]["isRunning"] = True          # 将当前会话状态设置为运行中
    bot: Chatbot = chat_dict[uid]["Chatbot"]     # 获取当前会话的Chatbot对象
    style: str = chat_dict[uid]["model"]         # 获取当前会话的对话样式
    try:                                    # 尝试获取bing的回复
        data = await bot.ask(prompt=msg, conversation_style=style)
    except Exception as e:                # 如果出现异常, 则返回异常信息, 并且将当前会话状态设置为未运行
        chat_dict[uid]["isRunning"] = False
        await bingchat.finish("askError: " + str(e), at_sender=True)
    chat_dict[uid]["isRunning"] = False     # 将当前会话状态设置为未运行
    if data["item"]["result"]["value"] != "Success":  # 如果返回的结果不是Success, 则返回错误信息, 并且删除当前会话
        await bingchat.send("返回Error: " + data["item"]["result"]["value"] + "请重试", at_sender=True)
        del chat_dict[uid]
        return

    throttling = data["item"]["throttling"]     # 获取当前会话的限制信息
    # 获取当前会话的最大对话数
    maxConversation = throttling["maxNumUserMessagesInConversation"]
    # 获取当前会话的当前对话数
    currentConversation = throttling["numUserMessagesInConversation"]
    if len(data["item"]["messages"]) < 2:       # 如果返回的消息数量小于2, 则说明会话已经中断, 则删除当前会话
        await bingchat.send("该对话已中断, 可能是被bing掐了, 请重试", at_sender=True)
        _ = await new_chat_(event=event, matcher=mathcer, user_id=uid)
        return
    # 如果返回的消息中没有text, 则说明提问了敏感问题, 则删除当前会话
    if "text" not in data["item"]["messages"][1]:
        await bingchat.send(data["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"], at_sender=True)
        return

    repMessage = swap_string_positions(
        data["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"])  # 获取bing的回复, 并且稍微处理一下
    try:                                # 尝试发送回复
        if maxConversation > currentConversation:   # 如果当前对话数小于最大对话数, 则正常发送
            await bingchat.send(repMessage + f"\n\n当前{currentConversation} 共 {maxConversation}", at_sender=True)
        else:                                # 如果当前对话数大于等于最大对话数, 先发送, 然后说不定帮你重置会话
            await bingchat.send(repMessage + f"\n\n当前{currentConversation} 共 {maxConversation}", at_sender=True)
            await bingchat.send("达到对话上限, 正帮你重置会话", at_sender=True)
            try:                # 因为重置会话可能遇到matcher.finish()的情况, 而finish()是通过抛出异常实现的, 我怕跑到下面的except里面去, 所以这里用try包一下, 然后直接return
                _ = await new_chat_(event=event, matcher=mathcer, user_id=uid)
            except:
                return
    except Exception as e:            # 如果发送失败, 则尝试把文字写在图片上发送
        try:
            await bingchat.send("文本消息被风控了, 这里咱尝试把文字写在图片上发送了"+MessageSegment.image(txt_to_png(repMessage)), at_sender=True)
        except Exception as eeee:   # 如果还是失败, 我也没辙了, 只能返回异常信息了
            await bingchat.send(f"消息全被风控了, 这是捕获的异常: {str(eeee)}", at_sender=True)


@reserve.handle()
async def _(matcher: Matcher, event: MessageEvent, msg: Message = CommandArg()):
    user_id = event.get_user_id()           # 获取用户id
    msg: str = msg.extract_plain_text()     # 获取用户消息
    # 如果用户消息不是balanced, creative, precise中的一个, 则按照creative处理
    if msg not in ["balanced", "creative", "precise"]:
        # 重置会话
        _ = await new_chat_(event=event, matcher=matcher, user_id=user_id)
        # 返回提示
        await reserve.finish("缺少参数或参数错误, 请使用 balanced 或者 creative 或 precise, 这里只能默认给你重置成creative")
    else:
        # 重置会话并返回提示
        await reserve.finish(await new_chat_(event=event, matcher=matcher, user_id=user_id))


@bingHelp.handle()
async def _():
    await bingHelp.finish(await getUsage())
