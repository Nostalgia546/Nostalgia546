# 个人主页维护

私有数据只展示贡献总量、按日贡献数、贡献类型和汇总语言字节量，不输出私有仓库名字、链接、描述、文件路径或提交消息。原版公开项目介绍保留。

## 数据口径

- 贡献：GitHub `contributionCalendar` 返回的最近一年日历，包含当前授权可见的私有贡献。
- 语言：Token 可访问的、自有且非 Fork 的仓库汇总，包含私有仓库。只开放部分仓库时，统计也只覆盖这些仓库。
- 语言统计排除 C++，剩余语言重新归一化；贡献日历仍包含旧项目贡献。
- 语言字节量不等于本人编写的代码量，也不表示熟练程度；仓库中的依赖或生成代码可能影响结果。
- 导出文件 `data/profile.json` 是允许公开的汇总数据；不保存原始 API 响应。

## 刷新

`scripts/collect_profile.py` 从环境变量 `PROFILE_STATS_TOKEN` 读取凭据，只向 GitHub 官方 API 发送。
随后执行 `scripts/render_classic_cards.py` 生成原版风格的统计卡片；`scripts/render_original_3d.cjs` 调用原版 0.7.1 渲染器生成绿色 3D 图。渲染器固定到提交 `fd54cf20784ed9a86dc7be48bb5eb1f74e92b4f8`，只收到已经匿名汇总的数据，不接触 Token。需要 Python、Node、绘图依赖和中文字体。

GitHub Actions 需要仓库 Secret `PROFILE_STATS_TOKEN`。它应使用仅能读取待统计仓库所需信息的令牌，不需要服务器、Cloudflare 或其他平台的权限。
Secret 没有配置时，工作流保留已有图片，不以公开数据覆盖包含私有仓库的快照。不要把 Token 写入代码或工作流文件。

GitHub 主页原生贡献日历的“显示私有贡献”是独立的个人设置；这套图片不会自动更改该设置。

## 外观

恢复原版居中标题、打字效果、技术徽章、绿色 3D 图和白色统计卡片。语言占比条使用 GIF，并提供显示最终数据的 PNG。
设置 `PROFILE_FONT` 和 `PROFILE_FONT_BOLD` 可以指定中文字体路径。Windows 默认使用微软雅黑，Linux 默认使用 Noto Sans CJK。
3D 图的语言饼图使用排除 C++ 后的字节占比；贡献雷达图仍使用真实贡献次数。
