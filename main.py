import asyncio
import json
import os
import time
from typing import Optional

import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.core.platform.message_type import MessageType
from astrbot.core.message.message_event_result import MessageChain

try:
    from astrbot.core.platform.astr_message_event import MessageSession
except ImportError:
    from astrbot.core.platform.message_session import MessageSession

BILIBILI_ROOM_API = "https://api.live.bilibili.com/room/v1/Room/get_info"
STATE_FILE = os.path.join(os.path.dirname(__file__), "_stream_state.json")


def load_state() -> dict:
    default_state = {
        "last_notify_time": 0,
        "last_status": None,
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                for key, value in default_state.items():
                    if key not in state:
                        state[key] = value
                return state
        except Exception as e:
            logger.error(f"加载状态文件失败: {e}")
    return default_state


def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存状态文件失败: {e}")


async def get_live_status(room_id: str) -> Optional[dict]:
    if not room_id:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BILIBILI_ROOM_API,
                params={"room_id": room_id},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://live.bilibili.com/",
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("code") == 0:
                        room_info = data.get("data", {}).get("room_info", {})
                        anchor_info = data.get("data", {}).get("anchor_info", {}).get("base_info", {})
                        return {
                            "live_status": room_info.get("live_status", 0),
                            "title": room_info.get("title", ""),
                            "uname": anchor_info.get("uname", ""),
                            "area_name": room_info.get("area_name", ""),
                            "cover": room_info.get("cover", ""),
                            "keyframe": room_info.get("keyframe", ""),
                            "face": anchor_info.get("face", ""),
                        }
    except Exception as e:
        logger.error(f"获取直播状态失败: {e}")
    return None


@register("stream_info", "StreamNotify", "Bilibili直播间开播检测与QQ群通知插件", "0.0.1", "https://github.com/aminobatlog/astrbot_plugin_stream_info")
class StreamInfoPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.state = load_state()
        self.check_task: Optional[asyncio.Task] = None
        self.running = False

    async def initialize(self):
        self.running = True
        self.check_task = asyncio.create_task(self._check_loop())
        logger.info("StreamInfo 插件已启动，开始监控直播状态")

    async def terminate(self):
        self.running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        logger.info("StreamInfo 插件已停止")

    async def _check_loop(self):
        while self.running:
            try:
                await self._check_and_notify()
            except Exception as e:
                logger.error(f"直播检测循环异常: {e}")
            check_interval = self.config.get("check_interval", 60)
            await asyncio.sleep(check_interval)

    async def _check_and_notify(self):
        room_id = self.config.get("room_id", "")
        if not room_id:
            return

        status_info = await get_live_status(room_id)
        if status_info is None:
            return

        current_status = status_info.get("live_status", 0) == 1
        last_status = self.state.get("last_status")
        now = time.time()
        cooldown_hours = self.config.get("cooldown_hours", 4)
        cooldown_seconds = cooldown_hours * 60 * 60

        if last_status is None:
            self.state["last_status"] = current_status
            save_state(self.state)
            return

        if current_status and not last_status:
            last_notify = self.state.get("last_notify_time", 0)
            if now - last_notify >= cooldown_seconds:
                await self._send_notify(is_online=True, status_info=status_info)
                self.state["last_notify_time"] = now
        elif not current_status and last_status:
            await self._send_notify(is_online=False, status_info=status_info)

        self.state["last_status"] = current_status
        save_state(self.state)

    async def _send_notify(self, is_online: bool, status_info: dict):
        groups = self.config.get("groups", [])
        if not groups:
            logger.warning("未配置通知群组，跳过通知发送")
            return

        room_id = self.config.get("room_id", "")
        from astrbot.core.message.components import Plain, Image
        
        if is_online:
            text = self.config.get("notify_text", "")
            title = status_info.get("title", "")
            uname = status_info.get("uname", "")
            area = status_info.get("area_name", "")
            cover = status_info.get("cover", "") or status_info.get("keyframe", "")
            link = f"https://live.bilibili.com/{room_id}"
            
            message_text = f"{text}\n\n🔴 主播: {uname}\n📺 标题: {title}\n🏷️ 分区: {area}\n\n👉 点击进入直播间: {link}"
            
            components = []
            if cover:
                components.append(Image.fromURL(cover))
            components.append(Plain(message_text))
            chain = MessageChain(components)
            
            for group_id in groups:
                try:
                    await self._send_to_group(str(group_id), chain)
                    logger.info(f"已向群 {group_id} 发送开播通知")
                except Exception as e:
                    logger.error(f"向群 {group_id} 发送通知失败: {e}")
        else:
            message = self.config.get("offline_text", "")
            chain = MessageChain([Plain(message)])
            
            for group_id in groups:
                try:
                    await self._send_to_group(str(group_id), chain)
                    logger.info(f"已向群 {group_id} 发送关播通知")
                except Exception as e:
                    logger.error(f"向群 {group_id} 发送通知失败: {e}")

    async def _send_to_group(self, group_id: str, chain: MessageChain):
        platforms = self.context.platform_manager.get_insts()
        for platform in platforms:
            platform_name = platform.meta().name.lower()
            if "onebot" in platform_name or "aiocqhttp" in platform_name or "napcat" in platform_name:
                try:
                    session = MessageSession(
                        platform_name=platform.meta().name,
                        message_type=MessageType.GROUP_MESSAGE,
                        session_id=group_id
                    )
                    await platform.send_by_session(session, chain)
                    return
                except Exception as e:
                    logger.debug(f"通过平台 {platform.meta().name} 发送失败: {e}")
                    continue
        raise Exception("未找到可用的 OneBot 平台")

    def _is_admin(self, user_id: str) -> bool:
        admins = self.config.get("admins", [])
        return str(user_id) in [str(a) for a in admins]

    @filter.command("stream")
    async def stream_command(self, event: AstrMessageEvent):
        """直播通知管理命令"""
        user_id = event.get_sender_id()
        if not self._is_admin(user_id):
            yield event.plain_result("你没有权限使用此命令")
            return

        message = event.message_str.strip()
        parts = message.split(maxsplit=2)

        if len(parts) < 2:
            yield event.plain_result(self._get_help())
            return

        sub_cmd = parts[1].lower()

        if sub_cmd == "text" and len(parts) >= 3:
            content = parts[2].strip().strip('"').strip("'")
            self.config["notify_text"] = content
            self.config.save_config()
            yield event.plain_result(f"开播通知内容已更新为:\n{content}")

        elif sub_cmd == "roomid" and len(parts) >= 3:
            room_id = parts[2].strip().strip('"').strip("'")
            if not room_id.isdigit():
                yield event.plain_result("直播间号必须是数字")
                return
            self.config["room_id"] = room_id
            self.state["last_status"] = None
            self.config.save_config()
            save_state(self.state)
            yield event.plain_result(f"已绑定直播间: {room_id}")

        elif sub_cmd == "noti":
            room_id = self.config.get("room_id", "")
            if not room_id:
                yield event.plain_result("请先绑定直播间号 (/stream roomid 房间号)")
                return
            status_info = await get_live_status(room_id)
            if status_info is None:
                yield event.plain_result("获取直播状态失败，请检查房间号")
                return
            is_online = status_info.get("live_status", 0) == 1
            await self._send_notify(is_online=is_online, status_info=status_info)
            yield event.plain_result("已手动发送直播通知")

        elif sub_cmd == "offinfo" and len(parts) >= 3:
            content = parts[2].strip().strip('"').strip("'")
            self.config["offline_text"] = content
            self.config.save_config()
            yield event.plain_result(f"关播通知内容已更新为:\n{content}")

        elif sub_cmd == "status":
            room_id = self.config.get("room_id", "")
            admins = self.config.get("admins", [])
            groups = self.config.get("groups", [])
            notify_text = self.config.get("notify_text", "")
            offline_text = self.config.get("offline_text", "")
            check_interval = self.config.get("check_interval", 60)
            cooldown_hours = self.config.get("cooldown_hours", 4)

            status_text = "当前配置:\n"
            status_text += f"直播间号: {room_id or '未设置'}\n"
            status_text += f"管理员: {', '.join(str(a) for a in admins) or '无'}\n"
            status_text += f"通知群: {', '.join(str(g) for g in groups) or '无'}\n"
            status_text += f"检测间隔: {check_interval}秒\n"
            status_text += f"通知冷却: {cooldown_hours}小时\n"
            status_text += f"开播通知: {notify_text}\n"
            status_text += f"关播通知: {offline_text}"
            yield event.plain_result(status_text)

        elif sub_cmd == "help":
            yield event.plain_result(self._get_help())

        else:
            yield event.plain_result(self._get_help())

    def _get_help(self) -> str:
        return """直播通知管理命令:
/stream text "内容" - 设置开播通知内容
/stream roomid "房间号" - 绑定直播间号
/stream noti - 手动触发通知
/stream offinfo "内容" - 设置关播通知内容
/stream status - 查看当前配置
/stream help - 显示此帮助

管理员和通知群请在AstrBot管理面板的插件配置中设置"""
