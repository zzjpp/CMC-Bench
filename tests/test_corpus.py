"""Release invariants that prevent silent shrinking, leakage and lost hard tiers."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from evaluate import ROOT, read_jsonl
EXCLUDED={(q['source_id'],q['number']) for q in json.loads((ROOT/'qa/exclusions.json').read_text(encoding='utf-8'))}


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items=read_jsonl(ROOT/'data/items.jsonl')

    def test_real_corpus_size_and_range(self):
        self.assertEqual(len(self.items),333)
        self.assertEqual({q['difficulty'] for q in self.items},set(range(1,9)))
        self.assertEqual({q['stage'] for q in self.items},{'预赛','决赛'})
        self.assertEqual(len({q['subject'] for q in self.items}),10)

    def test_quarantine_is_not_scored(self):
        for q in self.items:
            for o in q['source_occurrences']:
                self.assertNotIn((o['source_id'],o['number']),EXCLUDED)

    def test_all_splits_cover_all_tiers(self):
        for split in ['dev','validation','test']:
            items=[q for q in self.items if q['split']==split]
            self.assertEqual({q['difficulty'] for q in items},set(range(1,9)))
            inputs=read_jsonl(ROOT/f'data/inputs/{split}.jsonl')
            self.assertEqual({q['id'] for q in inputs},{q['id'] for q in items})
            self.assertTrue(all(set(q)=={'id','question','question_latex','assets'} for q in inputs))

    def test_original_gold_is_explicit_and_local(self):
        for q in self.items:
            if 'solution_source' in q:
                self.assertTrue((ROOT/q['solution_source']['path']).is_file())
                self.assertIn('item_localized',q['solution_source']['page_scope'])
            self.assertEqual(q['reference_solution_format'],'inline_full_solution')
            self.assertEqual(q['verification_status'],'single_agent_reviewed_not_human_certified')
            self.assertNotIn('解法提要：',q['reference_solution'])
            for block in q['question_latex'].split('$')[1::2]:
                self.assertEqual(block.count('{'),block.count('}'),q['id'])

    def test_source_normalizations_reach_the_solver(self):
        items={q['id']:q for q in self.items}
        self.assertIn('请给出一个',items['CMC-2018-FINAL-MathSenior-I-1']['question'])
        self.assertIn('C¹[0,1)',items['CMC-2018-FINAL-MathSenior-I-2']['question'])
        self.assertIn('f′=αf+βf″',items['CMC-2015-PRE-NonMath-III']['question'])


if __name__=='__main__':unittest.main()
