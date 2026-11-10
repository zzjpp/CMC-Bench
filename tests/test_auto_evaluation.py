"""Offline synthetic tests, including a real local HTTP transport round trip."""
import copy
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from common import ROOT,read_jsonl
from auto_evaluate import prepare,run,summarize,validate_judgment,validate_responses
from http_client import complete,digest,load_lines
from run_solver import run as solve


class AutoTests(unittest.TestCase):
    def setUp(self):
        self.temp_root=ROOT/'runs'
        self.temp_root.mkdir(exist_ok=True)
        self.items=read_jsonl(ROOT/'data/items.jsonl')[:3]
        self.responses=[dict(id=q['id'],response='SYNTHETIC RESPONSE FOR TESTING') for q in self.items]
        self.plan=prepare(self.items,self.responses)
        self.config=dict(endpoint='http://127.0.0.1:1/v1/chat/completions',model='synthetic',max_tokens=300,
                         token_parameter='max_completion_tokens',key_env='CMC_TEST_UNUSED_KEY',timeout=2,temperature=None)

    def grade(self,item,correct=True):
        return dict(criteria={c['id']:(c['points'] if correct else 0) for c in item['scoring_rubric']},
                    fully_correct=correct,critical_error=False,reference_issue=False,rationale='SYNTHETIC ONLY: criterion test')

    def journal(self,correct=True):
        items={q['id']:q for q in self.items}
        return [dict(id=r['id'],pass_number=r['pass_number'],request_sha256=r['request_sha256'],
                     plan_sha256=self.plan['plan_sha256'],judgment=self.grade(items[r['id']],correct),calls=[]) for r in self.plan['requests']]

    def test_perfect_and_zero_fixed_denominator(self):
        self.assertEqual(summarize(self.plan,self.journal())['overall']['strict_accuracy_bounds'],[1,1])
        self.assertEqual(summarize(self.plan,self.journal(False))['overall']['normalized_score_bounds'],[0,0])

    def test_missing_and_empty_are_zero(self):
        responses=[dict(id=self.items[0]['id'],response=''),self.responses[1]]
        plan=prepare(self.items,responses)
        self.assertEqual(len(plan['requests']),2)
        report=summarize(plan,[])
        self.assertEqual(report['overall']['n'],3)
        self.assertEqual(report['overall']['strict_accuracy_bounds'],[0,1/3])
        self.assertEqual(report['status_counts']['missing_response'],1)
        self.assertEqual(report['status_counts']['empty_response'],1)

    def test_disagreement_and_reference_issue_remain_unresolved(self):
        journal=self.journal()
        journal[1]['judgment']=self.grade(self.items[0],False)
        report=summarize(self.plan,journal)
        self.assertEqual(report['overall']['needs_review'],1)
        self.assertEqual(report['overall']['strict_accuracy_bounds'],[2/3,1])
        journal[1]['judgment']=self.grade(self.items[0])
        journal[1]['judgment'].update(reference_issue=True,fully_correct=False)
        self.assertEqual(summarize(self.plan,journal)['outcomes'][0]['reason'],'reference_or_statement_issue')

    def test_response_duplicate_unknown_and_extra_fields_rejected(self):
        for rows in [self.responses+[self.responses[0]],self.responses+[dict(id='unknown',response='x')],
                     [dict(self.responses[0],reference_solution='leak')]]:
            with self.assertRaises(ValueError):validate_responses(self.items,rows)

    def test_critical_error_and_boolean_points_rejected(self):
        g=self.grade(self.items[0]);g['critical_error']=True
        with self.assertRaises(ValueError):validate_judgment(self.items[0],g)
        g=self.grade(self.items[0]);g['criteria'][next(iter(g['criteria']))]=True
        with self.assertRaises(ValueError):validate_judgment(self.items[0],g)

    def test_journal_duplicates_wrong_hash_and_tampered_plan_rejected(self):
        journal=self.journal()
        with self.assertRaises(ValueError):summarize(self.plan,journal+[journal[0]])
        journal[0]['request_sha256']='0'*64
        with self.assertRaises(ValueError):summarize(self.plan,journal)
        plan=copy.deepcopy(self.plan);plan['entries'][0]['item']['final_answer']='tamper'
        with self.assertRaises(ValueError):summarize(plan,[])

    def test_retry_resume_and_changed_configuration(self):
        q=self.items[0];plan=prepare([q],[self.responses[0]])
        invalid=dict(ok=True,content='not JSON',usage=None,elapsed_seconds=0)
        good=dict(ok=True,content=json.dumps(self.grade(q)),usage=dict(prompt_tokens=5,completion_tokens=5,total_tokens=10),elapsed_seconds=0)
        with tempfile.TemporaryDirectory(dir=self.temp_root) as d,patch('auto_evaluate.complete',side_effect=[invalid,good,good]) as model:
            report=run(plan,d,self.config,attempts=2)
            self.assertEqual(model.call_count,3)
            self.assertEqual(report['overall']['strict_accuracy_bounds'],[1,1])
            self.assertEqual(report['transport_attempts'],3)
            self.assertIsNone(report['reported_usage']['total_tokens'])
            run(plan,d,self.config,attempts=2)
            self.assertEqual(model.call_count,3)
            with self.assertRaises(ValueError):run(plan,d,dict(self.config,model='changed'),attempts=2)

    def test_transport_failure_does_not_score_candidate_as_wrong(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as d,patch('auto_evaluate.complete',return_value=dict(ok=False,error='TimeoutError',usage=None,elapsed_seconds=0)):
            report=run(self.plan,d,self.config)
            self.assertEqual(report['overall']['strict_accuracy_bounds'],[0,1])
            self.assertEqual(report['overall']['needs_review'],3)

    def test_http_solver_to_judge_end_to_end_and_resume(self):
        item=self.items[0];grading=self.grade(item)
        calls=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                calls.append(body)
                content=json.dumps(grading) if body['model']=='synthetic-judge' else 'SYNTHETIC SOLVER RESPONSE'
                result=dict(model=body['model'],choices=[dict(message=dict(content=content),finish_reason='stop')],
                            usage=dict(prompt_tokens=5,completion_tokens=3,total_tokens=8))
                data=json.dumps(result).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            config=dict(self.config,endpoint=f'http://127.0.0.1:{server.server_port}/v1/chat/completions')
            with tempfile.TemporaryDirectory(dir=self.temp_root) as d:
                path=Path(d)/'inputs.jsonl'
                safe={k:item[k] for k in ['id','question','question_latex','assets']}
                path.write_text(json.dumps(safe,ensure_ascii=False)+'\n',encoding='utf-8')
                responses=solve(path,Path(d)/'solver',config)
                self.assertEqual(len(calls),1)
                # Solver wire payload never carries the reference or item metadata.
                self.assertEqual(calls[0]['messages'][1]['content'],item['question_latex'])
                self.assertNotIn(item['reference_solution'],json.dumps(calls[0],ensure_ascii=False))
                plan=prepare([item],load_lines(responses))
                result=run(plan,Path(d)/'judge',dict(config,model='synthetic-judge'))
                self.assertEqual(result['overall']['strict_accuracy_bounds'],[1,1])
                self.assertEqual(result['reported_usage']['total_tokens'],16)
                self.assertEqual(len(calls),3)
                solve(path,Path(d)/'solver',config)
                run(plan,Path(d)/'judge',dict(config,model='synthetic-judge'))
                self.assertEqual(len(calls),3)
        finally:server.shutdown();server.server_close();thread.join(timeout=2)


if __name__=='__main__':unittest.main()
