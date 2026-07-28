# LLLLL Skills

Claude Code 自定义技能集合。

## 包含技能

### learn-project

**通用课程学习助手** — 输入课程名，自动生成学习计划，逐日教学，带复习/测验/进度追踪。

**触发方式**：
- `/learn-project SQL`
- `我想学Python`
- `帮我制定数据库学习计划`

### adaptive-learning-coach

**自适应学习教练** — 诊断驱动、掌握度驱动的通用学习教练，支持编程、语言、考试、创作等主题。带间隔复习、项目实战和本地可移植状态。

**触发方式**：
- `/adaptive-learning-coach 6周学会SQL，每天45min`
- `/adaptive-learning-coach 继续昨天的英语训练`
- `帮我诊断Python基础，安排两周复习计划`

**功能**：
- 🎯 轻量诊断确定起点，而非自报水平
- 📋 里程碑 + 能力地图 + 交付物验收标准
- 🔄 间隔复习：按实际表现动态计算复习日期
- 📊 掌握度 + 记忆保持率 + 独立完成能力追踪
- 💾 项目内 JSON/Markdown 状态，可版本控制
- 🐍 配套 CLI 工具 `learning_state.py`，仅依赖 Python 标准库

## 安装

将 `learn-project/` 和 `adaptive-learning-coach/` 目录复制到 `~/.claude/skills/`：

```bash
cp -r learn-project ~/.claude/skills/
cp -r adaptive-learning-coach ~/.claude/skills/
```

## 使用

```
/learn-project <课程名>
/adaptive-learning-coach <学习目标>
```

## License

MIT
