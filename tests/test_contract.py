import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator', ROOT / 'validate.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.q = {'id': 'example', 'prompt': '2/3 × 3/5 = ?', 'options': ['5/8', '6/15', '2/5', '3/5'], 'correct': 2}
    def test_equivalent_answer_is_rejected(self):
        self.assertIn('EQUIVALENT_ANSWER', [c for c, _ in v.rendering_contract(self.q)])
    def test_explicit_simplest_form_is_allowed(self):
        self.q['prompt'] += ' Give the simplest form.'
        self.assertEqual(v.rendering_contract(self.q), [])
    def test_hidden_passage_is_rejected(self):
        self.q.update(passage='Mila found an egg under a tree.', options=['a','b','c','d'])
        self.assertIn('HIDDEN_PASSAGE', [c for c, _ in v.rendering_contract(self.q)])
    def test_visible_passage_is_allowed(self):
        self.q.update(passage='A story.', type='reading', options=['a','b','c','d'])
        self.assertEqual(v.rendering_contract(self.q), [])
    def test_release_contract(self):
        bank = json.loads((ROOT / 'questions.json').read_text())
        self.assertEqual(len(bank['questions']), 5479)
        for q in bank['questions']:
            self.assertEqual(v.rendering_contract(q), [], q['id'])

if __name__ == '__main__': unittest.main()
