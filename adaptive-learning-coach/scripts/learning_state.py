#!/usr/bin/env python3
"""Portable learning-state manager for adaptive-learning-coach."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
INVALID_PATH_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
SPACE_RUN = re.compile(r'\s+')
DASH_RUN = re.compile(r'-{2,}')


class StateError(RuntimeError):
    pass


def slugify(value: str) -> str:
    cleaned = INVALID_PATH_CHARS.sub('-', value.strip().lower())
    cleaned = SPACE_RUN.sub('-', cleaned)
    cleaned = DASH_RUN.sub('-', cleaned).strip(' .-')
    if cleaned in {'', '.', '..'}:
        digest = hashlib.sha1(value.encode('utf-8')).hexdigest()[:8]
        return f'course-{digest}'
    return cleaned[:80].rstrip(' .-')


def parse_day(value: str | None) -> date:
    if value is None:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise StateError(f'日期必须使用 YYYY-MM-DD：{value}') from exc


def course_dir(root: str | Path, slug: str) -> Path:
    safe = slugify(slug)
    if safe != slug:
        raise StateError(f'课程标识不安全或格式不规范：{slug}；建议使用：{safe}')
    return Path(root).expanduser().resolve() / safe


def state_path(root: str | Path, slug: str) -> Path:
    return course_dir(root, slug) / 'state.json'


def atomic_write_json(target: Path, payload: dict[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    temporary.replace(target)


def load_state(root: str | Path, slug: str) -> tuple[Path, dict[str, Any]]:
    target = state_path(root, slug)
    if not target.exists():
        raise StateError(f'未找到学习状态：{target}')
    try:
        state = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateError(f'无法读取状态文件：{target}') from exc
    validate_state(state)
    return target, state


def validate_state(state: dict[str, Any]) -> None:
    if not isinstance(state, dict):
        raise StateError('状态根节点必须是对象')
    if state.get('schema_version') != SCHEMA_VERSION:
        raise StateError(
            f"不支持的 schema_version：{state.get('schema_version')}，期望 {SCHEMA_VERSION}"
        )
    for key in ('course', 'progress', 'topics', 'history'):
        if key not in state:
            raise StateError(f'状态缺少字段：{key}')
    if not isinstance(state['topics'], dict) or not isinstance(state['history'], list):
        raise StateError('topics 必须是对象，history 必须是数组')
    progress = state['progress']
    for key in ('sessions_completed', 'total_minutes'):
        value = progress.get(key)
        if not isinstance(value, int) or value < 0:
            raise StateError(f'progress.{key} 必须是非负整数')
    for name, topic in state['topics'].items():
        mastery = topic.get('mastery')
        if not isinstance(mastery, (int, float)) or not 0 <= mastery <= 1:
            raise StateError(f'主题 {name} 的 mastery 必须在 0 到 1 之间')
        parse_day(topic.get('next_review'))


def render_plan(course_name: str) -> str:
    template = Path(__file__).resolve().parents[1] / 'assets' / 'course-plan-template.md'
    if template.exists():
        return template.read_text(encoding='utf-8').replace('{{course_name}}', course_name)
    return f'# {course_name} 学习计划\n'


def init_course(args: argparse.Namespace) -> int:
    slug = slugify(args.slug or args.course)
    folder = Path(args.root).expanduser().resolve() / slug
    target = folder / 'state.json'
    if target.exists() and not args.force:
        raise StateError(f'课程已存在：{target}。如需覆盖，请显式使用 --force。')

    created = parse_day(args.date)
    state = {
        'schema_version': SCHEMA_VERSION,
        'course': {
            'name': args.course,
            'slug': slug,
            'goal': args.goal,
            'level': args.level,
            'minutes_per_session': args.minutes,
            'weeks': args.weeks,
            'sessions_per_week': args.sessions_per_week,
            'created_at': created.isoformat(),
        },
        'progress': {
            'sessions_completed': 0,
            'total_minutes': 0,
            'last_session': None,
            'current_milestone': 'M1',
        },
        'topics': {},
        'history': [],
    }
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'sessions').mkdir(exist_ok=True)
    atomic_write_json(target, state)
    plan = folder / 'plan.md'
    if args.force or not plan.exists():
        plan.write_text(render_plan(args.course), encoding='utf-8')
    print(json.dumps({'course': args.course, 'slug': slug, 'path': str(folder)}, ensure_ascii=False))
    return 0


def schedule_topic(previous: dict[str, Any] | None, score: float, transfer: bool, day: date) -> dict[str, Any]:
    old = previous or {}
    old_mastery = float(old.get('mastery', 0.0))
    ease = float(old.get('ease', 2.3))
    repetitions = int(old.get('repetitions', 0))
    old_interval = int(old.get('interval_days', 0))

    if score < 60:
        repetitions = 0
        interval = 1
        ease = max(1.3, ease - 0.25)
    elif score < 80:
        repetitions = max(1, repetitions)
        interval = 2
        ease = max(1.3, ease - 0.1)
    else:
        repetitions += 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 3
        else:
            multiplier = ease * (1.15 if transfer and score >= 90 else 1.0)
            interval = max(4, round(max(old_interval, 3) * multiplier))
        if score >= 90:
            ease = min(3.0, ease + (0.08 if transfer else 0.04))

    observed = score / 100.0
    mastery = min(1.0, old_mastery * 0.65 + observed * 0.35 + (0.05 if transfer else 0.0))
    if mastery >= 0.85 and transfer and repetitions >= 2:
        level = 'mastered'
    elif mastery >= 0.7:
        level = 'working'
    else:
        level = 'fragile'

    return {
        'mastery': round(mastery, 4),
        'level': level,
        'ease': round(ease, 2),
        'repetitions': repetitions,
        'interval_days': interval,
        'last_score': round(score, 2),
        'last_review': day.isoformat(),
        'next_review': (day + timedelta(days=interval)).isoformat(),
        'transfer_observed': bool(transfer),
    }


def record_session(args: argparse.Namespace) -> int:
    target, state = load_state(args.root, args.slug)
    day = parse_day(args.date)
    topic_before = state['topics'].get(args.topic)
    topic_after = schedule_topic(topic_before, args.score, args.transfer, day)
    if args.confidence is not None:
        topic_after['confidence'] = args.confidence
    state['topics'][args.topic] = topic_after
    state['progress']['sessions_completed'] += 1
    state['progress']['total_minutes'] += args.minutes
    state['progress']['last_session'] = day.isoformat()
    state['history'].append({
        'date': day.isoformat(),
        'topic': args.topic,
        'score': round(args.score, 2),
        'minutes': args.minutes,
        'confidence': args.confidence,
        'transfer': bool(args.transfer),
        'note': args.note or '',
        'next_review': topic_after['next_review'],
    })
    atomic_write_json(target, state)
    print(json.dumps({'topic': args.topic, **topic_after}, ensure_ascii=False))
    return 0


def due_topics(state: dict[str, Any], day: date) -> list[dict[str, Any]]:
    result = []
    for name, topic in state['topics'].items():
        due = parse_day(topic['next_review'])
        if due <= day:
            result.append({'topic': name, **topic, 'days_overdue': (day - due).days})
    return sorted(result, key=lambda item: (-item['days_overdue'], item['mastery'], item['topic']))


def print_due(args: argparse.Namespace) -> int:
    _, state = load_state(args.root, args.slug)
    day = parse_day(args.date)
    items = due_topics(state, day)
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    elif not items:
        print('没有到期复习。')
    else:
        for item in items:
            print(
                f"- {item['topic']}: mastery={item['mastery']:.0%}, "
                f"score={item['last_score']:.0f}, overdue={item['days_overdue']}d"
            )
    return 0


def print_status(args: argparse.Namespace) -> int:
    _, state = load_state(args.root, args.slug)
    day = parse_day(args.date)
    topics = state['topics']
    weak = sorted(
        ({'topic': name, **value} for name, value in topics.items() if value['level'] == 'fragile'),
        key=lambda item: item['mastery'],
    )
    mastery_average = (
        sum(float(value['mastery']) for value in topics.values()) / len(topics)
        if topics else 0.0
    )
    payload = {
        'course': state['course'],
        'progress': state['progress'],
        'topic_count': len(topics),
        'average_mastery': round(mastery_average, 4),
        'weak_topics': [item['topic'] for item in weak],
        'due_topics': [item['topic'] for item in due_topics(state, day)],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"课程：{state['course']['name']}（{state['course']['goal']}）")
        print(
            f"进度：{state['progress']['sessions_completed']} 次会话，"
            f"{state['progress']['total_minutes']} 分钟"
        )
        print(f"平均掌握度：{payload['average_mastery']:.0%}")
        print('薄弱点：' + ('、'.join(payload['weak_topics']) if payload['weak_topics'] else '无已记录薄弱点'))
        print('到期复习：' + ('、'.join(payload['due_topics']) if payload['due_topics'] else '无'))
    return 0


def validate_command(args: argparse.Namespace) -> int:
    target, state = load_state(args.root, args.slug)
    validate_state(state)
    print(f'OK: {target}')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Manage adaptive learning state.')
    sub = parser.add_subparsers(dest='command', required=True)

    init = sub.add_parser('init', help='Initialize a course.')
    init.add_argument('--root', default='.learning')
    init.add_argument('--course', required=True)
    init.add_argument('--slug')
    init.add_argument('--goal', required=True)
    init.add_argument('--level', choices=('beginner', 'intermediate', 'advanced'), default='beginner')
    init.add_argument('--minutes', type=int, default=30)
    init.add_argument('--weeks', type=int, default=4)
    init.add_argument('--sessions-per-week', type=int, default=5)
    init.add_argument('--date')
    init.add_argument('--force', action='store_true')
    init.set_defaults(func=init_course)

    record = sub.add_parser('record', help='Record one topic-centered learning session.')
    record.add_argument('--root', default='.learning')
    record.add_argument('--slug', required=True)
    record.add_argument('--topic', required=True)
    record.add_argument('--score', type=float, required=True, metavar='0..100')
    record.add_argument('--minutes', type=int, default=30)
    record.add_argument('--confidence', type=int, choices=range(1, 6))
    record.add_argument('--transfer', action='store_true')
    record.add_argument('--note')
    record.add_argument('--date')
    record.set_defaults(func=record_session)

    due = sub.add_parser('due', help='List due review topics.')
    due.add_argument('--root', default='.learning')
    due.add_argument('--slug', required=True)
    due.add_argument('--date')
    due.add_argument('--json', action='store_true')
    due.set_defaults(func=print_due)

    status = sub.add_parser('status', help='Show course status.')
    status.add_argument('--root', default='.learning')
    status.add_argument('--slug', required=True)
    status.add_argument('--date')
    status.add_argument('--json', action='store_true')
    status.set_defaults(func=print_status)

    validate = sub.add_parser('validate', help='Validate a state file.')
    validate.add_argument('--root', default='.learning')
    validate.add_argument('--slug', required=True)
    validate.set_defaults(func=validate_command)
    return parser


def positive_ints(args: argparse.Namespace) -> None:
    score = getattr(args, 'score', None)
    if score is not None and not 0 <= score <= 100:
        raise StateError('--score 必须在 0 到 100 之间')
    for name in ('minutes', 'weeks', 'sessions_per_week'):
        value = getattr(args, name, None)
        if value is not None and value <= 0:
            raise StateError(f'--{name.replace("_", "-")} 必须大于 0')


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        positive_ints(args)
        return args.func(args)
    except StateError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
