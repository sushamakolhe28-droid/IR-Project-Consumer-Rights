import unittest
from src.forum_guidance import parse_monetary_amount, determine_forum, get_forum_guidance

class TestForumGuidance(unittest.TestCase):
    def test_delivered_date_no_amount(self):
        # "delivered on September 20, 2026" -> no amount
        text = "delivered on September 20, 2026"
        amounts = parse_monetary_amount(text)
        self.assertEqual(amounts, [], f"Expected no amount parsed from date, got {amounts}")
        
        guidance = get_forum_guidance(text)
        self.assertFalse(guidance["show_forum_box"], "Forum box must NOT be shown when no amount is found")
        self.assertIsNone(guidance["amount"])
        self.assertIsNone(guidance["forum_tier"])
        self.assertIsNone(guidance["forum_name"])
        self.assertIn("Section 69", guidance["limitation_source"])
        self.assertIn("Two years", guidance["limitation_note"])

    def test_paid_rs_1_5_crore_state_commission(self):
        # "paid Rs 1.5 crore" -> 1.5 crore -> State Commission
        text = "paid Rs 1.5 crore"
        amounts = parse_monetary_amount(text)
        self.assertTrue(len(amounts) > 0, "Expected amount to be parsed")
        val, raw = amounts[0]
        self.assertEqual(val, 15000000.0)
        self.assertEqual(raw, "Rs 1.5 crore")
        
        guidance = get_forum_guidance(text)
        self.assertTrue(guidance["show_forum_box"])
        self.assertEqual(guidance["amount"], 15000000.0)
        self.assertEqual(guidance["forum_tier"], "State Commission")
        self.assertIn("State Commission", guidance["forum_name"])
        self.assertIn("Rule 4", guidance["rule_source"])

    def test_paid_rs_45000_district_commission(self):
        # "paid Rs 45,000" -> District Commission
        text = "paid Rs 45,000"
        amounts = parse_monetary_amount(text)
        self.assertTrue(len(amounts) > 0, "Expected amount to be parsed")
        val, raw = amounts[0]
        self.assertEqual(val, 45000.0)
        self.assertEqual(raw, "Rs 45,000")
        
        guidance = get_forum_guidance(text)
        self.assertTrue(guidance["show_forum_box"])
        self.assertEqual(guidance["amount"], 45000.0)
        self.assertEqual(guidance["forum_tier"], "District Commission")
        self.assertIn("District Commission", guidance["forum_name"])
        self.assertIn("Rule 3", guidance["rule_source"])

    def test_3_crore_flat_national(self):
        # "3 crore flat" -> National
        text = "3 crore flat"
        amounts = parse_monetary_amount(text)
        self.assertTrue(len(amounts) > 0, "Expected amount to be parsed")
        val, raw = amounts[0]
        self.assertEqual(val, 30000000.0)
        self.assertEqual(raw, "3 crore")
        
        guidance = get_forum_guidance(text)
        self.assertTrue(guidance["show_forum_box"])
        self.assertEqual(guidance["amount"], 30000000.0)
        self.assertEqual(guidance["forum_tier"], "National Commission")
        self.assertIn("National", guidance["forum_name"])
        self.assertIn("Rule 5", guidance["rule_source"])

    def test_year_and_date_variations_no_amount(self):
        # 4-digit years (1900-2100) and dates without currency must never be parsed as amounts
        samples = [
            "2026",
            "in 2026",
            "year 2026",
            "20/09/2026",
            "September 20",
            "dated 15-08-2024",
            "on 2026-05-12",
            "between 2021 and 2023"
        ]
        for sample in samples:
            amounts = parse_monetary_amount(sample)
            self.assertEqual(amounts, [], f"Expected no amount for {sample!r}, got {amounts}")
            guidance = get_forum_guidance(sample)
            self.assertFalse(guidance["show_forum_box"], f"Expected show_forum_box=False for {sample!r}")
            self.assertIn("Section 69", guidance["limitation_source"])

    def test_date_and_amount_in_same_complaint(self):
        # A complaint with both date and amount should parse only the monetary amount
        text = "On September 20, 2026, I ordered a laptop for Rs 45,000 but received damaged goods."
        amounts = parse_monetary_amount(text)
        self.assertEqual(len(amounts), 1)
        self.assertEqual(amounts[0][0], 45000.0)
        
        guidance = get_forum_guidance(text)
        self.assertTrue(guidance["show_forum_box"])
        self.assertEqual(guidance["forum_tier"], "District Commission")

if __name__ == '__main__':
    unittest.main()
