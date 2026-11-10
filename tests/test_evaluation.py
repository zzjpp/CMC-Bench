"""Regression checks against inflated or unaudited benchmark scores."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from evaluate import read_jsonl, summarize, validate_grades, ROOT


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.items=[q for q in read_jsonl(ROOT/'data/items.jsonl') if q['split']=='test']
        self.grades=[dict(id=q['id'],criteria={c['id']:c['points'] for c in q['scoring_rubric']},
            fully_correct=True,critical_error=False,status='adjudicated',review_type='human',
            reviewer_ids=['synthetic-reviewer-1','synthetic-reviewer-2'],rationale='SYNTHETIC TEST ONLY',
            response_sha256='0'*64) for q in self.items]

    def test_perfect_and_zero_boundaries(self):
        self.assertEqual(summarize(self.items,self.grades)['strict_accuracy'],1)
        for g in self.grades:
            g.update(criteria={k:0 for k in g['criteria']},fully_correct=False)
        result=summarize(self.items,self.grades)
        self.assertEqual(result['normalized_score'],0)
        self.assertEqual(result['difficulty_macro_accuracy'],0)

    def test_missing_response_is_not_silently_removed(self):
        with self.assertRaises(ValueError):
            summarize(self.items,self.grades[:-1])

    def test_duplicate_response_rejected(self):
        with self.assertRaises(ValueError):
            summarize(self.items,self.grades+[self.grades[0]])

    def test_llm_cannot_be_final_adjudicator(self):
        self.grades[0]['review_type']='llm'
        with self.assertRaises(ValueError):
            summarize(self.items,self.grades)

    def test_critical_error_cannot_receive_full_credit(self):
        self.grades[0]['critical_error']=True
        with self.assertRaises(ValueError):
            summarize(self.items,self.grades)

    def test_one_person_cannot_count_as_two_reviewers(self):
        self.grades[0]['reviewer_ids']=['same','same']
        with self.assertRaises(ValueError):
            summarize(self.items,self.grades)

    def test_negative_oversized_and_boolean_scores_rejected(self):
        for bad in [-1,3,True]:
            grades=copy.deepcopy(self.grades)
            first=next(iter(grades[0]['criteria']))
            grades[0]['criteria'][first]=bad
            with self.assertRaises(ValueError):
                summarize(self.items,grades)

    def test_ability_uses_criterion_scores(self):
        report=summarize(self.items,self.grades)
        self.assertTrue(all(v['criterion_score']==1 for v in report['per_ability'].values()))
        self.assertIn('proxy',report['per_ability']['Mathematical Generalization']['interpretation'])

    def test_eight_level_macro_and_four_bands(self):
        report=summarize(self.items,self.grades)
        self.assertEqual(set(report['per_difficulty']),{f'L{i}' for i in range(1,9)})
        self.assertEqual(report['difficulty_macro_accuracy'],1)
        self.assertEqual(sum(x['n'] for x in report['per_difficulty_band'].values()),len(self.items))
        self.assertEqual(len(report['per_difficulty_band']),4)


if __name__=='__main__':
    unittest.main()
