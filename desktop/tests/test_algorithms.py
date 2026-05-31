import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from datetime import datetime
from algorithms import (
    compute_lps, kmp_search, search_medical_history,
    Appointment, greedy_schedule_optimization, find_conflicts,
    Medicament, optimize_prescriptions_dp, optimize_prescriptions_bruteforce,
    PatientHashTable, AVLTree, AVLNode, AppointmentHeap
)


class TestKMP(unittest.TestCase):
    def test_kmp_basic_match(self):
        occ = kmp_search("hello world", "world")
        self.assertEqual(occ, [6])

    def test_kmp_no_match(self):
        occ = kmp_search("hello world", "xyz")
        self.assertEqual(occ, [])

    def test_kmp_multiple_occurrences(self):
        occ = kmp_search("aaaaa", "aa")
        self.assertEqual(occ, [0, 1, 2, 3])

    def test_lps_table(self):
        lps = compute_lps("AAABAAA")
        self.assertEqual(lps, [0, 1, 2, 0, 1, 2, 3])

    def test_search_medical_history(self):
        consultations = [
            {"motif": "fievre", "diagnostic": "paludisme", "observations": "", "traitement": "", "symptomes": ""},
            {"motif": "toux", "diagnostic": "rhume", "observations": "", "traitement": "", "symptomes": ""},
        ]
        results = search_medical_history(consultations, "paludisme")
        self.assertEqual(len(results), 1)


class TestGreedy(unittest.TestCase):
    def test_greedy_selects_high_priority(self):
        appts = [
            Appointment(1, "09:00", "10:00", 5, "Urgence", "Alice"),
            Appointment(2, "09:30", "10:30", 1, "Routine", "Bob"),
            Appointment(3, "10:00", "11:00", 3, "Suivi", "Charlie"),
        ]
        selected, _ = greedy_schedule_optimization(appts)
        self.assertGreater(len(selected), 0)
        self.assertEqual(selected[0].priorite, 5)

    def test_find_conflicts_detects_overlap(self):
        appts = [
            Appointment(1, "09:00", "10:00", 3, "A"),
            Appointment(2, "09:30", "10:30", 3, "B"),
        ]
        conflicts = find_conflicts(appts)
        self.assertEqual(len(conflicts), 1)

    def test_no_conflicts(self):
        appts = [
            Appointment(1, "09:00", "10:00", 3, "A"),
            Appointment(2, "10:00", "11:00", 3, "B"),
        ]
        conflicts = find_conflicts(appts)
        self.assertEqual(len(conflicts), 0)


class TestDP(unittest.TestCase):
    def test_dp_selects_best_combination(self):
        meds = [
            Medicament("Paracetamol", 2000, 80, 7),
            Medicament("Ibuprofene", 3000, 90, 5),
            Medicament("Amoxicilline", 5000, 95, 10),
        ]
        result = optimize_prescriptions_dp(meds, 5000)
        self.assertGreater(result['total_efficacy'], 0)
        self.assertLessEqual(result['total_cost'], 5000)

    def test_dp_vs_bruteforce_same_result(self):
        meds = [
            Medicament("A", 1000, 50, 7),
            Medicament("B", 2000, 80, 5),
            Medicament("C", 1500, 70, 10),
        ]
        res_brute = optimize_prescriptions_bruteforce(meds, 3000)
        res_dp = optimize_prescriptions_dp(meds, 3000)
        self.assertEqual(res_brute['total_efficacy'], res_dp['total_efficacy'])

    def test_dp_empty_list(self):
        result = optimize_prescriptions_dp([], 5000)
        self.assertEqual(result['total_cost'], 0)
        self.assertEqual(result['total_efficacy'], 0)
        self.assertEqual(len(result['selected']), 0)


class TestHashTable(unittest.TestCase):
    def test_hash_insert_and_get(self):
        ht = PatientHashTable(size=10)
        ht.insert("P001", {"nom": "Alice", "age": 30})
        patient = ht.get("P001")
        self.assertIsNotNone(patient)
        self.assertEqual(patient["nom"], "Alice")

    def test_hash_get_nonexistent(self):
        ht = PatientHashTable(size=10)
        self.assertIsNone(ht.get("INEXISTANT"))

    def test_hash_delete(self):
        ht = PatientHashTable(size=10)
        ht.insert("P001", {"nom": "Alice"})
        ht.delete("P001")
        self.assertIsNone(ht.get("P001"))

    def test_hash_collision(self):
        ht = PatientHashTable(size=1)
        ht.insert("P001", {"nom": "Alice"})
        ht.insert("P002", {"nom": "Bob"})
        self.assertEqual(ht.get("P001")["nom"], "Alice")
        self.assertEqual(ht.get("P002")["nom"], "Bob")


class TestAVL(unittest.TestCase):
    def test_avl_insert_and_inorder(self):
        avl = AVLTree()
        now = datetime.now()
        avl.insert(now, {"id": 1})
        avl.insert(datetime(2025, 1, 1), {"id": 2})
        result = avl.inorder()
        self.assertEqual(len(result), 2)

    def test_avl_balanced_after_inserts(self):
        avl = AVLTree()
        base = datetime(2025, 1, 1)
        for i in range(10):
            avl.insert(datetime(2025, 1, i + 1), {"id": i})
        balance = avl._balance(avl.root)
        self.assertIn(balance, [-1, 0, 1])

    def test_avl_rotation_left(self):
        avl = AVLTree()
        for i in range(5, 0, -1):
            avl.insert(datetime(2025, 1, i), {"id": i})
        balance = avl._balance(avl.root)
        self.assertIn(balance, [-1, 0, 1])


class TestHeap(unittest.TestCase):
    def test_heap_priority_order(self):
        heap = AppointmentHeap()
        heap.push(3, "Routine")
        heap.push(1, "Urgence")
        heap.push(2, "Suivi")
        self.assertEqual(heap.pop(), "Urgence")
        self.assertEqual(heap.pop(), "Suivi")
        self.assertEqual(heap.pop(), "Routine")

    def test_heap_peek(self):
        heap = AppointmentHeap()
        heap.push(1, "Urgence")
        heap.push(5, "Routine")
        self.assertEqual(heap.peek(), "Urgence")

    def test_heap_empty(self):
        heap = AppointmentHeap()
        self.assertTrue(heap.is_empty())
        self.assertEqual(heap.pop(), None)


if __name__ == "__main__":
    unittest.main()
