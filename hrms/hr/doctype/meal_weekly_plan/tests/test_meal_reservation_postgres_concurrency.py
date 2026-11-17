import threading
import unittest
import uuid

import frappe
from frappe.tests.utils import FrappeTestCase

try:
	import psycopg2
	from psycopg2 import sql
	from psycopg2.extensions import ISOLATION_LEVEL_REPEATABLE_READ
except ImportError:
	psycopg2 = None

from hrms.hr.doctype.meal_weekly_plan.reservation_locking import (
	employee_day_write_barrier,
	plan_day_write_barrier,
)


class TestMealReservationPostgresConcurrency(FrappeTestCase):
	def setUp(self):
		if frappe.db.db_type != "postgres":
			self.skipTest("The concurrency guarantee under test is PostgreSQL-specific.")
		if psycopg2 is None:
			self.skipTest("psycopg2 is required for the PostgreSQL concurrency test.")

		self.schema = f"meal_reservation_race_{uuid.uuid4().hex}"
		connection = frappe.db.get_connection()
		try:
			with connection.cursor() as cursor:
				cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
				cursor.execute(
					sql.SQL("CREATE TABLE {}.{} (name text PRIMARY KEY)").format(
						sql.Identifier(self.schema), sql.Identifier("tabEmployee")
					)
				)
				cursor.execute(
					sql.SQL(
						"CREATE TABLE {}.{} (parent text, meal_date date, max_portions integer, "
						"PRIMARY KEY (parent, meal_date))"
					).format(sql.Identifier(self.schema), sql.Identifier("tabMeal Weekly Plan Item"))
				)
				cursor.execute(
					sql.SQL(
						"CREATE TABLE {}.{} (name text PRIMARY KEY, meal_plan text, company text, "
						"reservation_date date, employee text, reservation_status text)"
					).format(sql.Identifier(self.schema), sql.Identifier("tabMeal Reservation"))
				)
				cursor.execute(
					sql.SQL("INSERT INTO {}.{} (name) VALUES (%s), (%s)").format(
						sql.Identifier(self.schema), sql.Identifier("tabEmployee")
					),
					("EMP-1", "EMP-2"),
				)
				cursor.execute(
					sql.SQL(
						"INSERT INTO {}.{} (parent, meal_date, max_portions) "
						"VALUES (%s, %s, %s)"
					).format(sql.Identifier(self.schema), sql.Identifier("tabMeal Weekly Plan Item")),
					("PLAN-1", "2026-11-17", 1),
				)
			connection.commit()
		finally:
			connection.close()

	def tearDown(self):
		if getattr(self, "schema", None):
			connection = frappe.db.get_connection()
			try:
				with connection.cursor() as cursor:
					cursor.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(self.schema)))
				connection.commit()
			finally:
				connection.close()
		super().tearDown()

	def _connect_to_fixture_schema(self):
		connection = frappe.db.get_connection()
		connection.set_isolation_level(ISOLATION_LEVEL_REPEATABLE_READ)
		with connection.cursor() as cursor:
			cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
		connection.commit()
		return connection

	def _assert_stale_writer_is_rejected(self, barrier, count_filter, first_row, second_row):
		barrier_query, barrier_values = barrier
		barrier_query = barrier_query.replace("`", '"')
		count_query = f'SELECT count(*) FROM "tabMeal Reservation" WHERE {count_filter}'
		insert_query = (
			'INSERT INTO "tabMeal Reservation" '
			"(name, meal_plan, company, reservation_date, employee, reservation_status) "
			"VALUES (%s, %s, %s, %s, %s, %s)"
		)
		first_locked = threading.Event()
		second_has_snapshot = threading.Event()
		outcomes = {}
		worker_errors = []

		def first_transaction():
			connection = self._connect_to_fixture_schema()
			try:
				with connection.cursor() as cursor:
					cursor.execute(count_query, first_row["count_values"])
					cursor.execute(barrier_query, barrier_values)
					first_locked.set()
					if not second_has_snapshot.wait(10):
						raise TimeoutError("Second transaction did not establish its snapshot.")
					cursor.execute(insert_query, first_row["insert_values"])
				connection.commit()
				outcomes["first"] = "committed"
			except Exception as error:  # surfaced below with the other worker's outcome
				connection.rollback()
				worker_errors.append(error)
			finally:
				connection.close()

		def second_transaction():
			connection = self._connect_to_fixture_schema()
			try:
				if not first_locked.wait(10):
					raise TimeoutError("First transaction did not acquire its write barrier.")
				with connection.cursor() as cursor:
					cursor.execute(count_query, second_row["count_values"])
					second_has_snapshot.set()
					try:
						cursor.execute(barrier_query, barrier_values)
					except psycopg2.errors.SerializationFailure:
						connection.rollback()
						outcomes["second"] = "serialization_failure"
					else:
						cursor.execute(insert_query, second_row["insert_values"])
						connection.commit()
						outcomes["second"] = "committed"
			except Exception as error:  # surfaced below with the other worker's outcome
				connection.rollback()
				worker_errors.append(error)
			finally:
				connection.close()

		threads = [threading.Thread(target=first_transaction), threading.Thread(target=second_transaction)]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join(15)

		self.assertFalse(any(thread.is_alive() for thread in threads), "Concurrent transactions timed out.")
		self.assertEqual(worker_errors, [])
		self.assertEqual(outcomes, {"first": "committed", "second": "serialization_failure"})

		connection = self._connect_to_fixture_schema()
		try:
			with connection.cursor() as cursor:
				cursor.execute(count_query, first_row["count_values"])
				self.assertEqual(cursor.fetchone()[0], 1)
			connection.rollback()
		finally:
			connection.close()

	def test_employee_day_race_cannot_commit_two_active_reservations(self):
		self._assert_stale_writer_is_rejected(
			employee_day_write_barrier("EMP-1"),
			"employee=%s AND reservation_date=%s AND reservation_status IN ('Reserved', 'Delivered')",
			{
				"count_values": ("EMP-1", "2026-11-17"),
				"insert_values": ("MR-1", "PLAN-1", "COMPANY-1", "2026-11-17", "EMP-1", "Reserved"),
			},
			{
				"count_values": ("EMP-1", "2026-11-17"),
				"insert_values": ("MR-2", "PLAN-2", "COMPANY-1", "2026-11-17", "EMP-1", "Reserved"),
			},
		)

	def test_plan_day_race_cannot_exceed_max_portions(self):
		self._assert_stale_writer_is_rejected(
			plan_day_write_barrier("PLAN-1", "2026-11-17"),
			"meal_plan=%s AND reservation_date=%s AND reservation_status IN ('Reserved', 'Delivered')",
			{
				"count_values": ("PLAN-1", "2026-11-17"),
				"insert_values": ("MR-1", "PLAN-1", "COMPANY-1", "2026-11-17", "EMP-1", "Reserved"),
			},
			{
				"count_values": ("PLAN-1", "2026-11-17"),
				"insert_values": ("MR-2", "PLAN-1", "COMPANY-1", "2026-11-17", "EMP-2", "Reserved"),
			},
		)


if __name__ == "__main__":
	unittest.main()
