import unittest

import conflict_judge as cj


def table(conflict, consistent, finding):
    out = {}
    for w in ("A", "B"):
        out[w] = {}
        for i, (kind, _, _) in cj.ITEMS.items():
            if kind == "finding":
                out[w][i] = finding[i] if isinstance(finding, dict) else finding
            else:
                out[w][i] = conflict if kind == "conflict" else consistent
    return out


class Cards(unittest.TestCase):
    def test_every_card_passes_the_request_checks_in_both_wordings(self):
        for item_id in cj.ITEMS:
            for wording in cj.WORDINGS:
                body = cj.card(item_id, wording)
                self.assertEqual(body["model"], cj.PINNED_MODEL)
                self.assertTrue(body["state"]["passage_A"]["text"].strip())
                self.assertTrue(body["state"]["passage_B"]["text"].strip())

    def test_wordings_offer_the_same_options_in_a_different_order(self):
        a, b = (list(cj.WORDINGS[w]["criteria"]) for w in ("A", "B"))
        self.assertEqual(set(a), set(b))
        self.assertNotEqual(a, b)

    def test_known_conflicts_quote_the_earlier_revision(self):
        self.assertIn("written only by `loop.py`", cj.card("CX1", "A")["state"]["passage_A"]["text"])


class Built(unittest.TestCase):
    def test_twenty_bases_make_forty_pairs_with_no_source_tell(self):
        self.assertEqual(len(cj.BUILT), 40)
        for item_id in cj.BUILT:
            state = cj.card(item_id, "A")["state"]
            self.assertEqual(state["passage_A"]["source"], state["passage_B"]["source"])

    def test_each_base_sentence_is_in_its_file(self):
        for item_id in cj.BUILT:
            self.assertTrue(cj.card(item_id, "A")["state"]["passage_A"]["text"])

    def test_noul_card_passes_the_request_checks_and_note_is_added_on_request(self):
        self.assertEqual(cj.card("F10", "A", "noul")["questions"]["conflict"]["type"], "noul")
        self.assertIn("note", cj.card("F10", "A", "choice", True)["state"])
        self.assertNotIn("note", cj.card("F10", "A")["state"])


class Variants(unittest.TestCase):
    def test_every_task_card_carries_its_task_and_passes_the_request_checks(self):
        for item_id in cj.TASKS:
            body = cj.card(item_id, "A", "task")
            self.assertEqual(body["state"]["task"], cj.TASKS[item_id])

    def test_false_note_and_trim_change_the_card_and_leave_the_default_alone(self):
        plain = cj.card("CK1", "A")
        self.assertEqual(cj.card("CK1", "A", "choice", "false")["state"]["note"], cj.FALSE_NOTE)
        self.assertNotIn("note", plain["state"])
        self.assertLess(len(cj.card("CX1", "A", "choice", False, True)["state"]["passage_B"]["text"]),
                        len(cj.card("CX1", "A")["state"]["passage_B"]["text"]))

    def test_trimmed_passages_are_taken_from_the_files(self):
        for item_id in cj.TRIMS:
            self.assertTrue(cj.card(item_id, "A", "choice", False, True)["state"]["passage_B"]["text"].strip())


class NewShapes(unittest.TestCase):
    def test_every_extra_shape_passes_the_request_checks(self):
        for shape in cj.EXTRA:
            self.assertEqual(cj.card("CK1", "A", shape)["questions"]["conflict"]["type"], cj.EXTRA[shape]["type"])

    def test_p_break_reads_each_shape_by_meaning_not_by_name(self):
        choice = {"probabilities": {"k7": 0.1, "q2": 0.7, "m9": 0.2}, "choice": "q2"}
        self.assertEqual(cj.p_break("names_random", choice), 0.7)
        swapped = {"probabilities": {"cannot_both_be_followed": 0.2, "both_followable": 0.75, "silent": 0.05}}
        self.assertEqual(cj.p_break("names_swapped", swapped), 0.75)
        self.assertAlmostEqual(cj.p_break("always", {"noul": 0.9}), 0.1)
        self.assertEqual(cj.p_break("probe", {"noul": 0.9}), 0.9)

    def test_swapped_names_put_the_break_description_under_the_followable_name(self):
        crit = cj.EXTRA["names_swapped"]["criteria"]
        self.assertIn("breaking", crit["both_followable"])
        self.assertIn("at once", crit["cannot_both_be_followed"])

    def test_fix_pairs_build_and_the_after_text_differs_from_the_before_text(self):
        for base in cj.FIX_BASES:
            before, after = cj.card(base + "b", "A")["state"], cj.card(base + "a", "A")["state"]
            self.assertTrue(before["passage_A"]["text"] and after["passage_B"]["text"])
            self.assertNotEqual((before["passage_A"]["text"], before["passage_B"]["text"]),
                                (after["passage_A"]["text"], after["passage_B"]["text"]), base)


class Maths(unittest.TestCase):
    def test_auc_is_one_for_perfect_separation_and_half_for_ties(self):
        self.assertEqual(cj.auc([0.9, 0.8], [0.1, 0.2]), 1.0)
        self.assertEqual(cj.auc([0.5], [0.5]), 0.5)

    def test_rates_use_the_half_threshold(self):
        r = cj.rates([0.9, 0.4], [0.1, 0.6, 0.2, 0.3])
        self.assertEqual((r["sensitivity"], r["false_alarm"]), (0.5, 0.25))

    def test_leave_one_out_fails_when_one_control_carries_the_gap(self):
        ids = {"conflict": ["a", "b"], "consistent": ["c", "d"]}
        p = {w: {"a": 1.0, "b": 0.1, "c": 0.0, "d": 0.0} for w in ("A", "B")}
        result = {r["drop"]: r["passes"] for r in cj.loo(p, ids)}
        self.assertFalse(result["a"])
        self.assertTrue(result["b"])


class PassRule(unittest.TestCase):
    def test_valid_when_conflicts_beat_consistent_by_the_gap(self):
        self.assertTrue(cj.verdict(table(0.8, 0.2, 0.5))["valid"])

    def test_void_when_the_gap_is_too_small(self):
        self.assertFalse(cj.verdict(table(0.5, 0.3, 0.5))["valid"])

    def test_a_finding_is_flagged_only_above_the_consistent_ceiling(self):
        findings = {i: 0.9 if i == "F5" else 0.15 for i, v in cj.ITEMS.items() if v[0] == "finding"}
        self.assertEqual(cj.verdict(table(0.8, 0.2, findings))["flagged"], ["F5"])


if __name__ == "__main__":
    unittest.main()
