# LLLLL Skills

Claude Code 自定义技能集合。

## 包含技能

### learn-project

**通用课程学习助手** — 输入课程名，自动生成学习计划，逐日教学，带复习/测验/进度追踪。

**触发方式**：
- `/learn-project SQL`
- `我想学Python`
- `帮我制定数据库学习计划`

**功能**：
- 🎯 需求采集：基础水平、时长、目标、周期、学习方式
- 📋 自动生成结构化学习计划（保存到 `~/Desktop/学习笔记/`）
- 📖 逐日教学：前日回顾 → 新知识 → 实战练习 → 总结
- 🧪 复习三步法：选择题回忆 → 小测验 → 实战重做
- 📊 进度追踪：自动写入 memory，断点续学
- ⚠️ 薄弱点标记，后续自动加强

**计划结构**：
```
第1周：核心基础
第2周：进阶应用
...
每天：回顾(15min) → 新知 → 实战 → 总结
```

## 安装

将 `learn-project/` 目录复制到 `~/.claude/skills/`：

```bash
cp -r learn-project ~/.claude/skills/
```

## 使用

```
/learn-project <课程名>
```

## 添加新技能

在 `skills/` 下创建新目录，添加 `SKILL.md`（含 YAML frontmatter）：

```markdown
---
name: my-skill
description: Use when ...
---

# Skill 内容
```

## License

MIT
