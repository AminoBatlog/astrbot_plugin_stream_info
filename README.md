# AstrBot Bilibili 直播通知插件

一个用于 [AstrBot](https://github.com/Soulter/AstrBot) 的 Bilibili 直播间开播/关播检测与 QQ 群通知插件。

## 功能特性

- 自动检测 Bilibili 直播间开播/关播状态
- 开播时自动向指定 QQ 群发送通知（包含主播名、直播标题、分区、直播间链接）
- 关播时自动发送关播通知
- 支持自定义开播/关播通知内容
- 支持配置多个通知群
- 支持配置多个管理员
- 开播通知冷却机制，防止频繁开关播导致的重复通知
- 支持通过命令或 WebUI 管理配置

## 安装

### 方式一：通过 AstrBot 插件市场安装

在 AstrBot 管理面板的插件市场中搜索 `stream_info` 进行安装。

### 方式二：通过 GitHub 链接安装

在 AstrBot 管理面板中，使用 GitHub 仓库链接添加插件：

```
https://github.com/your-repo/astrbot_plugin_stream_info
```

## 配置说明

安装插件后，在 AstrBot 管理面板的 **插件管理 -> stream_info -> 配置** 中进行设置。

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| admins | list | 管理员 QQ 号列表，有权限使用管理命令 | [] |
| groups | list | 通知群号列表，接收直播通知的 QQ 群 | [] |
| room_id | string | B站直播间房间号 | "" |
| notify_text | text | 开播通知文本 | 【直播通知】主播开播啦！快来围观~ |
| offline_text | text | 关播通知文本 | 【直播通知】主播下播了，下次再见~ |
| check_interval | int | 直播状态检测间隔（秒） | 60 |
| cooldown_hours | int | 开播通知冷却时间（小时） | 4 |

### 配置示例

```json
{
  "admins": ["123456789", "987654321"],
  "groups": ["111222333", "444555666"],
  "room_id": "12345",
  "notify_text": "【直播通知】主播开播啦！快来围观~",
  "offline_text": "【直播通知】主播下播了，下次再见~",
  "check_interval": 60,
  "cooldown_hours": 4
}
```

## 使用方法

### 快速开始

1. 在 WebUI 配置页面添加管理员 QQ 号到 `admins` 列表
2. 添加需要接收通知的 QQ 群号到 `groups` 列表
3. 设置要监控的 B站直播间号 `room_id`
4. 保存配置，插件将自动开始监控

### 管理命令

管理员可通过私聊或群聊向机器人发送以下命令：

| 命令 | 说明 |
|------|------|
| `/stream text "内容"` | 设置开播通知内容 |
| `/stream roomid "房间号"` | 绑定 B站直播间号 |
| `/stream noti` | 手动触发一次通知（根据当前直播状态发送开播或关播通知） |
| `/stream offinfo "内容"` | 设置关播通知内容 |
| `/stream status` | 查看当前所有配置 |
| `/stream help` | 显示帮助信息 |

### 命令示例

```
/stream roomid 12345
/stream text 【开播啦】主播上线了，快来直播间玩~
/stream offinfo 【下播通知】今天的直播结束了，感谢大家的陪伴！
/stream noti
/stream status
```

## 通知格式

### 开播通知

```
【直播通知】主播开播啦！快来围观~
主播: XXX
标题: 今天来打游戏
分区: 网游
直播间: https://live.bilibili.com/12345
```

### 关播通知

```
【直播通知】主播下播了，下次再见~
```

## 工作原理

1. 插件启动后，按照配置的检测间隔（默认60秒）定时查询 B站直播间状态
2. 当检测到直播状态从"未开播"变为"开播"时，向所有配置的 QQ 群发送开播通知
3. 开播通知有冷却机制（默认4小时），防止主播频繁开关播导致的重复通知
4. 当检测到直播状态从"开播"变为"未开播"时，向所有配置的 QQ 群发送关播通知

## 依赖

- AstrBot >= 3.0.0
- aiohttp >= 3.8.0

## 消息平台支持

本插件基于 OneBot v11 协议（aiocqhttp 适配器），支持以下消息平台：

- NapCat
- Lagrange
- 其他兼容 OneBot v11 的实现

## 常见问题

### Q: 为什么没有收到通知？

1. 检查是否已配置 `groups`（通知群列表）
2. 检查是否已配置 `room_id`（直播间号）
3. 检查 AstrBot 是否已正确连接 OneBot 适配器
4. 查看 AstrBot 日志是否有错误信息

### Q: 如何获取 B站直播间号？

打开 B站直播间页面，URL 中的数字即为直播间号。例如 `https://live.bilibili.com/12345` 中的 `12345`。

### Q: 通知冷却时间是什么意思？

为防止主播频繁开关播（如网络问题、OBS 重启等）导致的重复通知，插件设置了开播通知冷却时间。在冷却时间内，即使检测到多次开播，也只会发送一次通知。默认冷却时间为4小时。

## 许可证

MIT License

## 致谢

- [AstrBot](https://github.com/Soulter/AstrBot) - 强大的多平台聊天机器人框架
- [Bilibili Live API](https://api.live.bilibili.com) - B站直播数据接口
