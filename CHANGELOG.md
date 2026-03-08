# Changelog

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且该项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.0.2] - 2026-03-04

### 新增

- 新增 `at_all` 配置项：开播通知时可选择 @全体成员（需要机器人有管理员权限）
- 新增 `debug_mode` 配置项：开启后在控制台输出 API 返回的详细信息，方便调试

### 优化

- 优化开播通知格式，使用更美观的文本排版
- 当主播名称获取失败时，自动隐藏主播信息行
- 直播间链接现在会被 QQ 自动识别为可点击链接

## [0.0.1] - 2026-03-04

### 新增

- 首次发布
- 支持检测 Bilibili 直播间开播/关播状态
- 自动发送开播/关播通知到指定 QQ 群
- 支持自定义开播/关播通知内容
- 支持配置多个管理员和通知群
- 开播通知 4 小时冷却机制，防止频繁通知
- 管理命令：`/stream text`、`/stream roomid`、`/stream noti`、`/stream offinfo`、`/stream status`、`/stream help`
