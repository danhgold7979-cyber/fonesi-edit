import itertools
import unittest
from fonesi_edit.matrix import Scene,History,generate,valid_next

class MatrixTests(unittest.TestCase):
    def setUp(self):self.scenes=(Scene('s1',('a','b')),Scene('s2',('c','d')));self.history=History(('s1','s2'))
    def test_exhaustive_small(self):
        result=generate(self.scenes,4,history=self.history)
        self.assertEqual(result.status,'COMPLETE');self.assertEqual(set(result.rows),set(itertools.product('ab','cd')))
    def test_deterministic(self):
        self.assertEqual(generate(self.scenes,3,history=self.history,seed=91),generate(self.scenes,3,history=self.history,seed=91))
    def test_history_not_reused(self):
        result=generate(self.scenes,4,history=History(('s1','s2'),(('a','c'),)))
        self.assertNotIn(('a','c'),result.rows);self.assertEqual(result.status,'SEARCH_LIMIT')
    def test_window_and_difference(self):
        scenes=tuple(Scene(f's{i}',tuple(str(x) for x in range(5))) for i in range(4));history=History(tuple(s.id for s in scenes))
        result=generate(scenes,10,history=history,window=2,different=4,scope='window',seed=7,budget=625)
        previous=[]
        for row in result.rows:
            self.assertTrue(valid_next(row,previous,window=2,different=4,scope='window'));previous.append(row)
        self.assertEqual(len(result.rows),len(set(result.rows)))
    def test_huge_space_bounded(self):
        scenes=tuple(Scene(f's{i}',tuple(str(x) for x in range(100))) for i in range(20))
        result=generate(scenes,2,history=History(tuple(s.id for s in scenes)),budget=50)
        self.assertLessEqual(result.examined,50);self.assertEqual(len(result.rows),2)
    def test_scope_mismatch(self):
        with self.assertRaises(ValueError):generate(self.scenes,1,history=History(('s2','s1')))
    def test_invalid_bool(self):
        with self.assertRaises(ValueError):generate(self.scenes,True,history=self.history)
    def test_cancel(self):
        result=generate(self.scenes,4,history=self.history,cancel=lambda:True)
        self.assertEqual(result.status,'CANCELED');self.assertEqual(result.examined,0)
    def test_not_invent_unsatisfiability(self):
        result=generate(self.scenes,4,history=self.history,window=3,budget=4)
        self.assertEqual(result.status,'SEARCH_LIMIT')
    def test_k_previous_independent_of_window(self):
        self.assertFalse(valid_next(('a','d'),[('a','c')],window=0,different=2,scope='previous'))

    def test_elapsed_budget_is_not_unsat(self):
        from unittest.mock import patch
        with patch('fonesi_edit.matrix.time.monotonic',side_effect=[0,10]):
            result=generate(self.scenes,4,history=self.history,timeout_ms=1)
        self.assertEqual(result.status,'SEARCH_LIMIT');self.assertEqual(result.examined,0)
