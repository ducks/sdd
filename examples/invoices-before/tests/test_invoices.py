import unittest
from invoices import render_invoice

class InvoiceTests(unittest.TestCase):
    def test_integer_totals(self):
        self.assertEqual(render_invoice({'id':'INV-7','currency':'CZK','lines':[{'cents':100},{'cents':205}]}),
                         {'invoice':'INV-7','currency':'CZK','total_cents':305})
    def test_bad_currency(self):
        with self.assertRaises(ValueError):
            render_invoice({'id':'x','currency':'INVALID','lines':[{'cents':1}]})
    def test_bad_amount(self):
        with self.assertRaises(ValueError):
            render_invoice({'id':'x','currency':'USD','lines':[{'cents':True}]})
