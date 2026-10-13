import json
from pathlib import Path
import unittest

from hrms import hooks


class TestHRMSAppRoutes(unittest.TestCase):
	def test_hr_app_links_to_the_current_human_resources_workspace(self):
		expected_route = "/desk/human-resources"
		icon_path = Path(__file__).resolve().parents[1] / "desktop_icon" / "frappe_hr.json"
		icon = json.loads(icon_path.read_text())

		self.assertEqual(hooks.app_home, expected_route)
		self.assertEqual(hooks.add_to_apps_screen[0]["route"], expected_route)
		self.assertEqual(icon["link"], expected_route)
