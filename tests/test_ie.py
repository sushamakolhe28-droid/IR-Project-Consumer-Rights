import unittest
from src.ie import extract_entities, extract_amount, extract_platform, extract_items, extract_refund_status

class TestIE(unittest.TestCase):
    def test_extract_amount(self):
        self.assertEqual(extract_amount("I paid Rs. 5,000 for this."), 5000)
        self.assertEqual(extract_amount("The cost was ₹ 1.5 lakh"), 150000)
        self.assertEqual(extract_amount("It is worth 2 crore rupees"), 20000000)
        self.assertEqual(extract_amount("I paid Rs 50"), 50)
        
    def test_extract_platform(self):
        self.assertEqual(extract_platform("Ordered from amazon yesterday"), "Amazon")
        self.assertEqual(extract_platform("Swiggy didn't deliver my food"), "Swiggy")
        
    def test_extract_items(self):
        expected, received = extract_items("I ordered an iPhone but received a soap bar.")
        self.assertEqual(expected, "an iPhone")
        self.assertEqual(received, "a soap bar")
        
    def test_extract_refund_status(self):
        self.assertEqual(extract_refund_status("They refused refund completely"), "refused")
        self.assertEqual(extract_refund_status("Got refunded yesterday"), "refunded")
        self.assertEqual(extract_refund_status("My refund is pending"), "pending")

    def test_extract_entities_full(self):
        text = "I ordered a laptop but received a book from Flipkart on 12th May. I paid ₹ 50,000. They refused refund."
        entities = extract_entities(text)
        self.assertEqual(entities['amount'], 50000)
        self.assertEqual(entities['seller_platform'], "Flipkart")
        self.assertEqual(entities['expected_item'], "a laptop")
        self.assertEqual(entities['received_item'], "a book")
        self.assertEqual(entities['refund_status'], "refused")

if __name__ == '__main__':
    unittest.main()
