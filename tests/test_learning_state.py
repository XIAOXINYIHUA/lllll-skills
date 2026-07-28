from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'adaptive-learning-coach' / 'scripts' / 'learning_state.py'
SPEC = importlib.util.spec_from_file_location('learning_state', SCRIPT)
assert SPEC and SPEC.loader
learning_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(learning_state)


class LearningStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / '.learning'

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = learning_state.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def initialize(self) -> str:
        code, output, error = self.run_cli(
            'init', '--root', str(self.root), '--course', 'SQL 基础',
            '--goal', '完成数据分析项目', '--date', '2026-01-01'
        )
        self.assertEqual(code, 0, error)
        return json.loads(output)['slug']

    def test_slugify_is_safe_and_keeps_unicode(self) -> None:
        self.assertEqual(learning_state.slugify(' SQL 基础 '), 'sql-基础')
        self.assertEqual(learning_state.slugify('A/B:C'), 'a-b-c')
        self.assertTrue(learning_state.slugify('...').startswith('course-'))

    def test_init_creates_portable_state_and_plan(self) -> None:
        slug = self.initialize()
        folder = self.root / slug
        self.assertTrue((folder / 'state.json').exists())
        self.assertTrue((folder / 'plan.md').exists())
        self.assertTrue((folder / 'sessions').is_dir())
        state = json.loads((folder / 'state.json').read_text(encoding='utf-8'))
        self.assertEqual(state['course']['goal'], '完成数据分析项目')
        self.assertEqual(state['progress']['sessions_completed'], 0)

    def test_init_refuses_silent_overwrite(self) -> None:
        self.initialize()
        code, _, error = self.run_cli(
            'init', '--root', str(self.root), '--course', 'SQL 基础',
            '--goal', '另一个目标', '--date', '2026-01-02'
        )
        self.assertEqual(code, 2)
        self.assertIn('已存在', error)

    def test_record_low_score_schedules_next_day(self) -> None:
        slug = self.initialize()
        code, output, error = self.run_cli(
            'record', '--root', str(self.root), '--slug', slug,
            '--topic', 'JOIN', '--score', '55.5', '--minutes', '40',
            '--date', '2026-01-01'
        )
        self.assertEqual(code, 0, error)
        result = json.loads(output)
        self.assertEqual(result['next_review'], '2026-01-02')
        self.assertEqual(result['level'], 'fragile')

        code, output, error = self.run_cli(
            'due', '--root', str(self.root), '--slug', slug,
            '--date', '2026-01-02', '--json'
        )
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)[0]['topic'], 'JOIN')

    def test_repeated_transfer_can_reach_mastery(self) -> None:
        slug = self.initialize()
        for day in ('2026-01-01', '2026-01-02', '2026-01-05', '2026-01-12'):
            code, _, error = self.run_cli(
                'record', '--root', str(self.root), '--slug', slug,
                '--topic', '查询设计', '--score', '95', '--minutes', '30',
                '--date', day, '--transfer'
            )
            self.assertEqual(code, 0, error)
        state = json.loads((self.root / slug / 'state.json').read_text(encoding='utf-8'))
        self.assertEqual(state['topics']['查询设计']['level'], 'mastered')
        self.assertGreaterEqual(state['topics']['查询设计']['mastery'], 0.85)

    def test_validation_rejects_invalid_mastery(self) -> None:
        slug = self.initialize()
        target = self.root / slug / 'state.json'
        state = json.loads(target.read_text(encoding='utf-8'))
        state['topics']['坏数据'] = {'mastery': 2, 'next_review': '2026-01-01'}
        target.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
        code, _, error = self.run_cli('validate', '--root', str(self.root), '--slug', slug)
        self.assertEqual(code, 2)
        self.assertIn('mastery', error)


if __name__ == '__main__':
    unittest.main()
