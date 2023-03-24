# nonebot_plugin_newbingChat
使用了new bing + [EdgeGPT](https://github.com/acheong08/EdgeGPT) 的nonebot2插件, 支持多cookie同时配置, 有多少账号能拿多少
由于触发条件比较简单, 适合自己注册多账号配置, 如果单账号被大量使用, 容易被bing暂时限制
此仓库不再更新, 请左转https://github.com/Special-Week/nonebot_plugin_smart_reply




功能:

    调用new bing进行对话, 支持上下文, 单账号, 其他人无法插嘴
    at机器人 + 内容, 机器人即可相应
    一定时间内一个账号只能创建一个聊天对象, 防止滥用(su任意)
    通过由on_command生成的响应器 "重置会话", 可直接重置会话, 重新创建聊天对象


## 重要! cookie配置:

    0. 也许需要科学上网
    1. 使用这个插件必须配置cookie, 这个cookie内容过多不适合在.env, 所以这个cookie将会与json文件的形式进行配置
    2. 首先你需要一个通过申请的账号, 使用edge浏览器安装"editthiscookie"浏览器插件, 或者使用相关的其他插件获取cookie. 进入"bing.com/chat"登录通过的账号
    3. 右键界面选择"editthiscookie", 找到一个看上去像出门的样子的图标"导出cookie", cookie一般就能在你的剪贴板, 注意了, cookie导出来是一个list, 大概长这样[{},{},{}]
    4. 新建cookiexxx.json文件(xxx为任意合法字符), 把你剪贴板的cookie的字符串粘贴进去, 再次强调json大概长[{},{},{}]这样
    5. 打开你bot项目文件夹, 依次进入data/new_bing, 没有就新建, 把json文件丢进去, 有几个账号可以放几个, 要求cookie开头, .json结尾, 载入插件时初始化会全部读取, 创建会话的时候会通过random来选择一个账号的cookie
    6. 注意观察加载插件的时候, log会提示你加载了几个cookie

安装第三方依赖: 

    pip install EdgeGPT
    pip install loguru
    pip install pillow
    
    一直报错切cookie确认无误, 请尝试更新EdgeGPT(pip install EdgeGPT --upgrade)后再提issue


安装方式:

    download zip
    git clone https://github.com/Special-Week/nonebot_plugin_newbingChat.git
    剩下的你手动解决


env配置项目:
>以下配置项均可不填，插件会按照默认值读取

|config             |type            |default    |example                                  |usage                                   |
|-------------------|----------------|-----------|-----------------------------------------|----------------------------------------|
|cdtime             |int             |1800       |cdtime  = 114514               |一定时间内只能创建一个聊天对象|
|bot_nickname       |str             |"Hinata"    |bot_nickname = "Hinata"               |你bot的昵称, 回复的时候bing会替换成你bot的昵称  |




响应器如下:

    bingchat = on_message(rule=to_me(), priority=1145141919810, block=False)
    reserve = on_command("重置会话", aliases={"重置bing"}, priority=10, block=True)
    bingHelp = on_command("bing帮助", aliases={"binghelp"}, priority=10, block=True)
