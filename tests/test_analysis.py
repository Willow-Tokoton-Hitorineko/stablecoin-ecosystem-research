import copy
import json
import unittest
from pathlib import Path
from analysis import analyze

class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parents[1]/'samples/synthetic.json').read_text())
    def test_business_evidence_and_missingness(self):
        r = analyze(self.data)
        self.assertEqual(r['eligible_companies'], 3)
        self.assertEqual(r['pending_review_ids'], ['C05'])
        self.assertEqual(r['eligible_deals'], 3)
        self.assertEqual(r['missing_amount_deals'], 1)
        self.assertEqual(r['reported_amount_by_currency'], {'EUR':'500000','USD':'1200000'})
    def test_duplicate_company(self):
        self.data['companies'].append(copy.deepcopy(self.data['companies'][0]))
        with self.assertRaises(ValueError): analyze(self.data)
    def test_dangling_relation(self):
        self.data['deals'][0]['company_id']='UNKNOWN'
        with self.assertRaises(ValueError): analyze(self.data)
    def test_unknown_label(self):
        self.data['companies'][0]['labels']=['fintech']
        with self.assertRaises(ValueError): analyze(self.data)
    def test_nonfinite_amount(self):
        self.data['deals'][0]['amount']='NaN'
        with self.assertRaises(ValueError): analyze(self.data)
    def test_duplicate_deal(self):
        self.data['deals'].append(copy.deepcopy(self.data['deals'][0]))
        with self.assertRaises(ValueError): analyze(self.data)
    def test_input_unchanged(self):
        old=copy.deepcopy(self.data); analyze(self.data)
        self.assertEqual(self.data,old)

if __name__=='__main__': unittest.main()
