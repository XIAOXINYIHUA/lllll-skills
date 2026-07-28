# LLLLL Skills

Claude Code 自定义技能集合。

## 包含技能

### learn-project

**通用课程学习助手** — 输入课程名，自动生成学习计划，逐日教学，带复习/测验/进度追踪。

- `/learn-project SQL`
- `/learn-project 帮我制定数据库学习计划`

### adaptive-learning-coach

**自适应学习教练** — 诊断驱动、掌握度驱动的通用学习教练，支持编程、语言、考试、创作等主题。

- `/adaptive-learning-coach 6周学会SQL，每天45min`
- `/adaptive-learning-coach 继续昨天的英语训练`

### safe-github-publish

**安全 GitHub 发布工具** — 隐私扫描 + 自动清理敏感信息，把项目安全发布到 GitHub。

- `/safe-github-publish /path/to/project`
- `把这个项目上传到 GitHub`

### gpt-5-6-sol-prompting

**GPT-5.6 Sol 提示词工程** — 创建、优化、审查和迁移生产级 GPT-5.6 Sol 提示词。

- `/gpt-5-6-sol-prompting 帮我写一个代码审查提示词`
- `/gpt-5-6-sol-prompting 优化这个 system prompt`

## 安装

将需要的 skill 目录复制到 `~/.claude/skills/`：

```bash
cp -r learn-project ~/.claude/skills/
cp -r adaptive-learning-coach ~/.claude/skills/
cp -r safe-github-publish ~/.claude/skills/
cp -r gpt-5-6-sol-prompting ~/.claude/skills/
```

## License

MIT
