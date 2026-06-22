---
name: learn-project
description: Use when user wants to learn any course or skill — gathers requirements, generates learning plan with review cycles, and teaches day-by-day. Triggered by "我想学", "学习计划", "/learn-project".
---

# Learn Project

## Overview

Complete learning system: gather needs → generate plan → teach daily with review/quiz/practice → track progress.

**Core principle**: Every session = **Review → Learn → Practice**. No new knowledge without verifying the old.

## Flow

```
1. Check if plan already exists (search ~/Desktop/学习笔记/)
   ├─ Yes → ask: continue or regenerate?
   └─ No → proceed to step 2
2. Gather needs (AskUserQuestion, batch of 3 then 2)
3. Confirm needs → generate plan → save to ~/Desktop/学习笔记/<课程名>学习计划.md
4. Ask: start learning now?
5. Daily teaching mode (review → learn → practice → summary)
6. Update progress in memory after each day
```

## Step 1: Gather Needs

Batch 1 (AskUserQuestion, 3 questions):
- 基础水平: 零基础 / 有基础 / 进阶
- 每日时长: 1h / 2h / 4h+
- 学习目标: 就业 / 考试 / 兴趣 / 项目驱动

Batch 2 (AskUserQuestion, 2 questions):
- 学习周期: 1周 / 2周 / 1个月
- 学习方式: 理论优先 / 实战优先 / 均衡

After collecting, confirm with user before generating plan.

## Step 2: Generate Plan

Save to `~/Desktop/学习笔记/<课程名>学习计划.md`.

**Plan rules:**
1. Every day has fixed structure: 前日回顾 → 新知 → 实战 → 总结
2. Review uses 三步法: 选择题回忆 → 小测验 → 实战重做
3. Progressive difficulty: 概念 → 跟做 → 独立 → 综合
4. Weekly comprehensive review on last day of each week
5. Every 3-4 days, a big review covering all previous content
6. All code examples must be complete and runnable (no pseudocode)
7. Mark core knowledge with ← symbol
8. Include ⚠️ 常见错误 section for each day

## Step 3: Daily Teaching

When user says "继续学习" or "学下一天":

### Daily Structure

```
📋 前日回顾 (15min)
├─ AskUserQuestion: 3 道选择题回顾昨日概念
├─ 小测验: 1-2 道填空/简答/写代码（文本输出）
└─ 实战重做: 不看答案重写昨日核心练习

📖 今日新知
├─ 概念讲解（简洁，不超过必要长度）
├─ 代码示例（完整可运行）
└─ 常见错误/注意事项

🔧 实战练习
├─ 跟做练习（有参考）
└─ 独立练习（无参考）

📝 今日总结
├─ 关键收获（3-5 点）
├─ 薄弱点标记（如有）
└─ 明日预告
```

### Review Rules

- Use AskUserQuestion with exactly 3 options per question
- Correct → brief confirmation
- Wrong → explain correct answer, note as weak point
- If >1 wrong → spend extra time reviewing that topic
- If practice is struggling → provide more guided examples

## Step 4: Progress Tracking

After each day, write/update memory file:

```
name: <课程名>-learning-progress
description: <课程名>学习进度追踪
metadata: { type: project }
```

Content: current day, total days, start date, last study date, weak points.

When user returns, read this memory to resume from correct day.

## Rules

1. One question at a time during needs gathering (batch max 3 per AskUserQuestion call)
2. Always review before new content — no exceptions
3. All code must be runnable — no pseudocode
4. All communication in Chinese
5. Save plans to ~/Desktop/学习笔记/
6. Mark weak points for revisit
7. Weekly comprehensive review on day 5 of each week
