import unittest
from invoice_guard import money, normalized_key, supplier_invoice_fingerprint, audit_invoice_totals


class InvoiceGuardTest(unittest.TestCase):
    def test_number_parsing(self):
        self.assertEqual(str(money('1 234,56 €')), '1234.56')
        self.assertEqual(str(money('12.40')), '12.40')
        self.assertIsNone(money('NaN'))

    def test_fingerprint(self):
        self.assertEqual(supplier_invoice_fingerprint('Métro', 'F-002/26'), supplier_invoice_fingerprint('METRO', 'F00226'))
        self.assertIsNone(supplier_invoice_fingerprint('Métro', 'N/A'))
        self.assertEqual(normalized_key('été'), 'ETE')

    def test_ok(self):
        self.assertEqual(audit_invoice_totals({'total_ht':'20,00', 'total_ttc':'22,00','produits':[{'quantite':2,'prix_unitaire':10,'prix_total':20}]}), [])

    def test_bad_vat(self):
        result = audit_invoice_totals({'total_ht':100,'total_ttc':141})
        self.assertIn('unusual_tax', [x['code'] for x in result])

    def test_bad_lines(self):
        result = audit_invoice_totals({'total_ht':100,'produits':[{'quantite':2,'prix_unitaire':10,'prix_total':25}]})
        self.assertIn('line_mismatch', [x['code'] for x in result])
        self.assertIn('subtotal_mismatch', [x['code'] for x in result])

    def test_partial_ocr_does_not_flag_unreliable_sum(self):
        result = audit_invoice_totals({'total_ht':100,'produits':[{'quantite':None,'prix_unitaire':10}]})
        self.assertNotIn('subtotal_mismatch',[x['code'] for x in result])


if __name__ == '__main__':
    unittest.main()
