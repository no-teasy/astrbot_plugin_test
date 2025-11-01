import random
from datetime import datetime
from aiocqhttp import CQHttp
import aiocqhttp
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.config.astrbot_config import AstrBotConfig
import astrbot.api.message_components as Comp
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.message.message_event_result import MessageEventResult

# 点赞成功回复
success_responses = [
    "👍{total_likes}",
    "赞了赞了",
    "点赞成功！",
    "给{username}点了{total_likes}个赞",
    "赞送出去啦！一共{total_likes}个哦！",
    "为{username}点赞成功！总共{total_likes}个！",
    "点了{total_likes}个，快查收吧！",
    "赞已送达，请注意查收~ 一共{total_likes}个！",
    "给{username}点了{total_likes}个赞，记得回赞哟！",
    "赞了{total_likes}次，看看收到没？",
    "点了{total_likes}赞，没收到可能是我被风控了",
]

# 点赞数到达上限回复
limit_responses = [
    "今天给{username}的赞已达上限",
    "赞了那么多还不够吗？",
    "{username}别太贪心哟~",
    "今天赞过啦！",
    "今天已经赞过啦~",
    "已经赞过啦~",
    "还想要赞？不给了！",
    "已经赞过啦，别再点啦！",
]

# 陌生人点赞回复
stranger_responses = [
    "不加好友不赞",
    "我和你有那么熟吗？",
    "你谁呀？",
    "你是我什么人凭啥要我赞你？",
    "不想赞你这个陌生人",
    "我不认识你，不赞！",
    "加我好友了吗就想要我赞你？",
    "滚！",
]


@register(
    "astrbot_plugin_test",
    "no-teasy",
    "发送 赞我 自动点赞",
    "1.0.9",
    "https://github.com/no-teasy/astrbot_plugin_test",
)
class zanwo(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.success_responses: list[str] = success_responses

    async def _like(self, client: CQHttp, user_id: str) -> str:
        """
        给单个用户点赞
        :param client: CQHttp客户端
        :param user_id: 用户ID
        """
        total_likes = 0
        username = (await client.get_stranger_info(user_id=int(user_id))).get(
            "nickname", "未知用户"
        )
        for _ in range(5):
            try:
                await client.send_like(user_id=int(user_id), times=10)  # 点赞10次
                total_likes += 10
            except aiocqhttp.exceptions.ActionFailed as e:
                error_message = str(e)
                if "已达" in error_message:
                    error_reply = random.choice(limit_responses)
                elif "权限" in error_message:
                    error_reply = "你设了权限不许陌生人赞你"
                else:
                    error_reply = random.choice(stranger_responses)
                break

        reply = random.choice(self.success_responses) if total_likes > 0 else error_reply

        # 替换占位符
        if "{username}" in reply:
            reply = reply.replace("{username}", username)
        if "{total_likes}" in reply:
            reply = reply.replace("{total_likes}", str(total_likes))

        return reply

    @filter.regex(r"^赞.*")
    async def like_me(self, event: AiocqhttpMessageEvent):
        """给发送者点赞"""
        sender_id = event.get_sender_id()
        client = event.bot
        result = await self._like(client, sender_id)
        yield event.plain_result(result)

    @filter.llm_tool(name="like_me")
    async def like_me(self, event: AstrMessageEvent, random: int) -> MessageEventResult:
        """为发送者点赞
        
        Args: 
        random 随机数字
        """
        if not event.get_platform_name() == "aiocqhttp":
            return
        assert isinstance(event, AiocqhttpMessageEvent)
        client = event.bot
        sender_id = event.get_sender_id()
        result = await self._like(client, sender_id)
        yield event.plain_result(result)