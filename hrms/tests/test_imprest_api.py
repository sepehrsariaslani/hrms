import frappe
from frappe.tests.utils import FrappeTestCase

from hrms.api.imprest import classify_transaction, parse_payload


class TestImprestApi(FrappeTestCase):
	def test_parse_payload_accepts_json_string(self):
		payload = parse_payload('{"payment_type":"Pay","amount":1000}')
		self.assertEqual(payload.get("payment_type"), "Pay")
		self.assertEqual(payload.get("amount"), 1000)

	def test_parse_payload_rejects_invalid_json(self):
		self.assertRaises(frappe.ValidationError, parse_payload, "{invalid}")

	def test_classify_internal_transfer_for_owned_accounts(self):
		transaction_type = classify_transaction(
			"Internal Transfer",
			"Cash - _TC",
			"Bank - _TC",
			{"Cash - _TC", "Bank - _TC"},
		)
		self.assertEqual(transaction_type, "transfer")
