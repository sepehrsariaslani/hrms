import csv
import os
import re
import unicodedata
from datetime import date
from dataclasses import dataclass
from difflib import SequenceMatcher

import frappe
import jdatetime
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

DEFAULT_CSV_PATH = "/Users/sepehr/Downloads/frappe-bench/apps/hrms/hrms/api/Merged_Data.csv"
DEFAULT_HEALTH_INSURANCE_PROVIDER = "تامین اجتماعی"
DEFAULT_BANK_NAME = "بانک مهر ایران"
DEFAULT_BANK_ACCOUNT_TYPE = "قرض‌الحسنه"

PERSIAN_CHAR_MAP = str.maketrans(
	{
		"ي": "ی",
		"ى": "ی",
		"ئ": "ی",
		"ك": "ک",
		"ة": "ه",
		"ۀ": "ه",
		"ؤ": "و",
		"\u200c": " ",
		"\u200f": "",
		"\u200e": "",
	}
)
PERSIAN_DIGITS_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
NON_ALNUM_RE = re.compile(r"[^0-9A-Za-z\u0600-\u06FF]+")

EMPLOYEE_CUSTOM_FIELDS = {
	"Employee": [
		{
			"fieldname": "custom_national_id_code",
			"label": "کد ملی",
			"fieldtype": "Data",
			"insert_after": "cell_number",
			"in_list_view": 1,
		},
		{
			"fieldname": "custom_father_name",
			"label": "نام پدر",
			"fieldtype": "Data",
			"insert_after": "custom_national_id_code",
		},
	]
}
NATIONAL_ID_FIELDS = {
	"national_identity_number",
	"national_id",
	"national_id_no",
	"national_code",
	"custom_national_code",
	"custom_national_id",
	"custom_national_id_code",
}


@dataclass
class Candidate:
	name: str
	employee_name: str
	first_name: str
	last_name: str
	full_name_compact: str
	first_name_compact: str
	last_name_compact: str
	last_name_tokens: tuple[str, ...]
	id_values: list[str]


def normalize_text(value) -> str:
	text = str(value or "").strip()
	if not text or text.lower() in {"nan", "none", "null"}:
		return ""
	text = unicodedata.normalize("NFKC", text)
	text = text.translate(PERSIAN_CHAR_MAP).translate(PERSIAN_DIGITS_MAP)
	text = text.replace("‌", " ")
	text = re.sub(r"\s+", " ", text).strip()
	return text


def compact_text(value) -> str:
	text = normalize_text(value)
	if not text:
		return ""
	text = NON_ALNUM_RE.sub("", text)
	return text


def tokenize_text(value) -> tuple[str, ...]:
	return tuple(part for part in normalize_text(value).split(" ") if part)


def normalize_numeric(value, keep_plus: bool = False) -> str:
	text = normalize_text(value).replace(",", "")
	if not text:
		return ""
	if re.fullmatch(r"-?\d+\.0+", text):
		text = text.split(".", 1)[0]
	if keep_plus:
		return re.sub(r"[^\d+]", "", text)
	return re.sub(r"\D", "", text)


def normalize_national_code(value) -> str:
	digits = normalize_numeric(value)
	if not digits:
		return ""
	# Keep national code strictly 10 digits via left zero-padding.
	return digits.zfill(10)[-10:]


def normalize_phone_number(value) -> str:
	digits = normalize_numeric(value)
	if not digits:
		return ""
	# Common Iran mobile shape in CSV is 10 digits without leading zero.
	if len(digits) == 10 and digits.startswith("9"):
		return "0" + digits
	# Handle +98 / 98 prefixed numbers.
	if digits.startswith("98") and len(digits) >= 12:
		candidate = digits[2:]
		if len(candidate) == 10 and candidate.startswith("9"):
			return "0" + candidate
	return digits


def parse_bool(value) -> bool:
	if isinstance(value, bool):
		return value
	return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _ensure_employee_custom_fields():
	create_custom_fields(EMPLOYEE_CUSTOM_FIELDS, update=True)
	frappe.clear_cache(doctype="Employee")


def _pick_existing_fields(meta, candidates: list[str]) -> list[str]:
	available = {f.fieldname for f in meta.fields}
	return [fieldname for fieldname in candidates if fieldname in available]


def _parse_date_to_iso(value) -> str:
	normalized = normalize_text(value)
	if not normalized:
		return ""
	normalized = normalized.replace("-", "/")
	parts = normalized.split("/")
	if len(parts) != 3 or not all(part.isdigit() for part in parts):
		return ""

	year, month, day = [int(part) for part in parts]
	try:
		if year >= 1600:
			return date(year, month, day).isoformat()
		return jdatetime.date(year, month, day).togregorian().isoformat()
	except ValueError:
		return ""


def _build_company_lookup() -> dict[str, str]:
	lookup: dict[str, str] = {}
	for company_name in frappe.get_all("Company", pluck="name"):
		normalized = compact_text(company_name)
		if normalized:
			lookup[normalized] = company_name
	return lookup


def _resolve_company_name(raw_value: str, company_lookup: dict[str, str]) -> str:
	normalized = compact_text(raw_value)
	if not normalized:
		return ""
	return company_lookup.get(normalized, "")


def _resolve_default_company() -> str:
	companies = frappe.get_all("Company", pluck="name")
	if len(companies) == 1:
		return companies[0]
	return frappe.defaults.get_user_default("Company") or (companies[0] if companies else "")


def _ensure_designation(designation_name: str, dry_run: bool) -> str:
	designation_name = normalize_text(designation_name)
	if not designation_name:
		return ""
	if frappe.db.exists("Designation", designation_name):
		return designation_name
	existing = frappe.db.get_value("Designation", {"designation_name": designation_name}, "name")
	if existing:
		return existing
	if dry_run:
		return designation_name
	doc = frappe.get_doc({"doctype": "Designation", "designation_name": designation_name})
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_health_insurance_provider(provider_name: str, dry_run: bool) -> str:
	if not frappe.db.exists("DocType", "Employee Health Insurance"):
		return ""
	if frappe.db.exists("Employee Health Insurance", provider_name):
		return provider_name
	existing = frappe.db.get_value(
		"Employee Health Insurance",
		{"health_insurance_name": provider_name},
		"name",
	)
	if existing:
		return existing
	if dry_run:
		return provider_name
	doc = frappe.get_doc(
		{
			"doctype": "Employee Health Insurance",
			"health_insurance_name": provider_name,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_bank(bank_name: str, dry_run: bool) -> str:
	if frappe.db.exists("Bank", bank_name):
		return bank_name
	existing = frappe.db.get_value("Bank", {"bank_name": bank_name}, "name")
	if existing:
		return existing
	if dry_run:
		return bank_name
	doc = frappe.get_doc({"doctype": "Bank", "bank_name": bank_name})
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_bank_account_type(account_type: str, dry_run: bool) -> str:
	if not frappe.db.exists("DocType", "Bank Account Type"):
		return ""
	if frappe.db.exists("Bank Account Type", account_type):
		return account_type
	existing = frappe.db.get_value("Bank Account Type", {"account_type": account_type}, "name")
	if existing:
		return existing
	if dry_run:
		return account_type
	doc = frappe.get_doc({"doctype": "Bank Account Type", "account_type": account_type})
	doc.insert(ignore_permissions=True)
	return doc.name


def _load_rows(csv_path: str) -> list[dict]:
	with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
		return list(csv.DictReader(csv_file))


def _build_candidates() -> tuple[list[Candidate], list[str]]:
	employee_meta = frappe.get_meta("Employee")
	id_field_candidates = _pick_existing_fields(
		employee_meta,
		[
			"national_identity_number",
			"national_id",
			"national_id_no",
			"national_code",
			"custom_national_code",
			"custom_national_id",
			"custom_national_id_code",
			"health_insurance_no",
			"employee_number",
		],
	)

	fields = [
		"name",
		"employee_name",
		"first_name",
		"middle_name",
		"last_name",
		"cell_number",
		"company",
	] + id_field_candidates

	rows = frappe.get_all("Employee", fields=fields, limit_page_length=0)
	candidates: list[Candidate] = []
	for row in rows:
		first_name = normalize_text(row.get("first_name"))
		last_name = normalize_text(" ".join(filter(None, [row.get("middle_name"), row.get("last_name")])))
		employee_name = normalize_text(row.get("employee_name")) or normalize_text(
			" ".join(filter(None, [row.get("first_name"), row.get("last_name")]))
		)
		id_values = []
		for fieldname in id_field_candidates:
			if fieldname in NATIONAL_ID_FIELDS:
				cleaned = normalize_national_code(row.get(fieldname))
			else:
				cleaned = normalize_numeric(row.get(fieldname))
			if cleaned:
				id_values.append(cleaned)
		candidates.append(
			Candidate(
				name=row["name"],
				employee_name=employee_name,
				first_name=first_name,
				last_name=last_name,
				full_name_compact=compact_text(employee_name),
				first_name_compact=compact_text(first_name),
				last_name_compact=compact_text(last_name),
				last_name_tokens=tokenize_text(last_name),
				id_values=id_values,
			)
		)
	return candidates, id_field_candidates


def _similarity(left: str, right: str) -> float:
	if not left or not right:
		return 0.0
	return SequenceMatcher(None, left, right).ratio()


def _token_match_score(tokens_a: tuple[str, ...], tokens_b: tuple[str, ...]) -> float:
	if not tokens_a or not tokens_b:
		return 0.0
	set_a = set(tokens_a)
	set_b = set(tokens_b)
	intersection = len(set_a.intersection(set_b))
	if not intersection:
		return 0.0
	smaller = min(len(set_a), len(set_b))
	if intersection == smaller:
		# Allow one-token differences like "پلخوابی" vs "حسن پلخوابی".
		if abs(len(set_a) - len(set_b)) <= 1:
			return 0.96
		return 0.90
	return intersection / max(len(set_a), len(set_b))


def _resolve_employee(row: dict, candidates: list[Candidate], threshold: float) -> tuple[str, str, float, str]:
	first_name = normalize_text(row.get("نام"))
	last_name = normalize_text(row.get("نام خانوادگی"))
	full_name = normalize_text(" ".join(filter(None, [first_name, last_name])))
	full_name_compact = compact_text(full_name)
	first_compact = compact_text(first_name)
	last_compact = compact_text(last_name)
	last_tokens = tokenize_text(last_name)
	national_code = normalize_national_code(row.get("کد ملی"))

	by_national: dict[str, list[Candidate]] = {}
	by_full: dict[str, list[Candidate]] = {}
	by_first_last: dict[tuple[str, str], list[Candidate]] = {}
	by_first: dict[str, list[Candidate]] = {}

	for candidate in candidates:
		for id_value in candidate.id_values:
			by_national.setdefault(id_value, []).append(candidate)
		if candidate.full_name_compact:
			by_full.setdefault(candidate.full_name_compact, []).append(candidate)
		if candidate.first_name_compact or candidate.last_name_compact:
			by_first_last.setdefault(
				(candidate.first_name_compact, candidate.last_name_compact), []
			).append(candidate)
		if candidate.first_name_compact:
			by_first.setdefault(candidate.first_name_compact, []).append(candidate)

	if national_code and len(national_code) >= 8:
		matched = by_national.get(national_code, [])
		if len(matched) == 1:
			return matched[0].name, "national_code", 1.0, ""
		if len(matched) > 1:
			return "", "ambiguous", 0.0, f"multiple employees with national code {national_code}"

	if full_name_compact and len(by_full.get(full_name_compact, [])) == 1:
		matched = by_full[full_name_compact][0]
		return matched.name, "full_name_exact", 0.99, ""

	key = (first_compact, last_compact)
	if (first_compact or last_compact) and len(by_first_last.get(key, [])) == 1:
		matched = by_first_last[key][0]
		return matched.name, "first_last_exact", 0.98, ""

	pool = by_first.get(first_compact, []) if first_compact else []
	if not pool:
		pool = candidates

	scored = []
	for candidate in pool:
		score_full = _similarity(full_name_compact, candidate.full_name_compact)
		score_last = _similarity(last_compact, candidate.last_name_compact)
		score_tokens = _token_match_score(last_tokens, candidate.last_name_tokens)
		first_bonus = 0.12 if first_compact and first_compact == candidate.first_name_compact else 0.0
		score = max(score_full, (score_last * 0.75) + first_bonus, (score_tokens * 0.9) + first_bonus)
		scored.append((score, candidate))

	scored.sort(key=lambda item: item[0], reverse=True)
	best_score, best_candidate = scored[0]
	second_score = scored[1][0] if len(scored) > 1 else 0.0

	if best_score >= threshold and (best_score - second_score >= 0.04):
		return best_candidate.name, "fuzzy_name", round(best_score, 4), ""
	if best_score >= 0.82 and (best_score - second_score < 0.04):
		return "", "ambiguous", round(best_score, 4), (
			f"close match candidates for {full_name or first_name}: "
			f"{best_candidate.employee_name} ({best_score:.3f}) vs second ({second_score:.3f})"
		)
	return "", "not_found", round(best_score, 4), f"best score below threshold: {best_score:.3f}"


def _upsert_bank_account(
	employee_doc,
	deposit_no: str,
	bank_name: str,
	bank_account_type: str,
	dry_run: bool,
):
	if not deposit_no:
		return "skipped_no_deposit", ""

	conflict = frappe.db.get_value(
		"Bank Account",
		{
			"party_type": "Employee",
			"is_company_account": 0,
			"bank_account_no": deposit_no,
			"party": ("!=", employee_doc.name),
		},
		["name", "party"],
		as_dict=True,
	)
	if conflict:
		return "conflict", f"bank account {deposit_no} already linked to {conflict.party}"

	existing = frappe.db.get_value(
		"Bank Account",
		{
			"party_type": "Employee",
			"party": employee_doc.name,
			"is_company_account": 0,
			"bank_account_no": deposit_no,
		},
		"name",
	)

	bank_meta = frappe.get_meta("Bank Account")
	account_payload = {
		"account_name": f"حساب {employee_doc.employee_name or employee_doc.name}",
		"bank": bank_name,
		"bank_account_no": deposit_no,
		"party_type": "Employee",
		"party": employee_doc.name,
		"is_company_account": 0,
	}
	if bank_meta.has_field("account_type") and bank_account_type:
		account_payload["account_type"] = bank_account_type
	if bank_meta.has_field("company") and employee_doc.get("company"):
		account_payload["company"] = employee_doc.company

	default_exists = frappe.db.exists(
		"Bank Account",
		{"party_type": "Employee", "party": employee_doc.name, "is_company_account": 0, "is_default": 1},
	)
	if bank_meta.has_field("is_default"):
		account_payload["is_default"] = 0 if default_exists else 1

	if dry_run:
		return ("update" if existing else "create"), ""

	if existing:
		account_doc = frappe.get_doc("Bank Account", existing)
		changed = False
		for fieldname, value in account_payload.items():
			if account_doc.get(fieldname) != value:
				account_doc.set(fieldname, value)
				changed = True
		if changed:
			account_doc.save(ignore_permissions=True)
		return "update", ""

	account_doc = frappe.get_doc({"doctype": "Bank Account", **account_payload})
	account_doc.insert(ignore_permissions=True)
	return "create", ""


def _create_employee_from_row(
	row: dict,
	company_name: str,
	national_id_field: str,
	father_field: str,
	date_of_birth_field: str,
	designation_name: str,
	dry_run: bool,
):
	first_name = normalize_text(row.get("نام"))
	last_name = normalize_text(row.get("نام خانوادگی"))
	full_name = normalize_text(" ".join(filter(None, [first_name, last_name])))
	national_code = normalize_national_code(row.get("کد ملی"))
	phone_number = normalize_phone_number(row.get("شماره تماس"))
	father_name = normalize_text(row.get("نام پدر"))
	birth_date_iso = _parse_date_to_iso(row.get("تاریخ تولد"))

	if not first_name and not full_name:
		return None
	if national_id_field and national_code:
		existing = frappe.db.get_value("Employee", {national_id_field: national_code}, "name")
		if existing:
			return frappe.get_doc("Employee", existing)

	if dry_run:
		return frappe._dict({"name": f"NEW::{full_name}", "employee_name": full_name, "company": company_name})

	doc = frappe.new_doc("Employee")
	doc.naming_series = "HR-EMP-"
	doc.first_name = first_name or full_name
	doc.last_name = last_name
	doc.employee_name = full_name or doc.first_name
	doc.company = company_name or _resolve_default_company()
	doc.status = "Active"
	if designation_name:
		doc.designation = designation_name
	if date_of_birth_field and birth_date_iso:
		doc.set(date_of_birth_field, birth_date_iso)
	if father_field and father_name:
		doc.set(father_field, father_name)
	if national_id_field and national_code:
		doc.set(national_id_field, national_code)
	if phone_number:
		doc.cell_number = phone_number

	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	return doc


def _candidate_from_employee(employee_doc, id_fields: list[str]) -> Candidate:
	first_name = normalize_text(employee_doc.get("first_name"))
	last_name = normalize_text(
		" ".join(filter(None, [employee_doc.get("middle_name"), employee_doc.get("last_name")]))
	)
	employee_name = normalize_text(employee_doc.get("employee_name")) or normalize_text(
		" ".join(filter(None, [employee_doc.get("first_name"), employee_doc.get("last_name")]))
	)
	id_values = []
	for fieldname in id_fields:
		if fieldname in NATIONAL_ID_FIELDS:
			cleaned = normalize_national_code(employee_doc.get(fieldname))
		else:
			cleaned = normalize_numeric(employee_doc.get(fieldname))
		if cleaned:
			id_values.append(cleaned)

	return Candidate(
		name=employee_doc.name,
		employee_name=employee_name,
		first_name=first_name,
		last_name=last_name,
		full_name_compact=compact_text(employee_name),
		first_name_compact=compact_text(first_name),
		last_name_compact=compact_text(last_name),
		last_name_tokens=tokenize_text(last_name),
		id_values=id_values,
	)


def _sync_candidate_cache(
	candidates: list[Candidate],
	candidate_indexes: dict[str, int],
	employee_doc,
	id_fields: list[str],
):
	candidate = _candidate_from_employee(employee_doc, id_fields)
	index = candidate_indexes.get(candidate.name)
	if index is None:
		candidate_indexes[candidate.name] = len(candidates)
		candidates.append(candidate)
		return
	candidates[index] = candidate


def sync_employee_insurance_and_bank_data(
	csv_path=DEFAULT_CSV_PATH,
	dry_run=1,
	health_insurance_provider=DEFAULT_HEALTH_INSURANCE_PROVIDER,
	bank_name=DEFAULT_BANK_NAME,
	bank_account_type=DEFAULT_BANK_ACCOUNT_TYPE,
	fuzzy_threshold=0.88,
	create_missing=0,
	update_name_fields=1,
):
	dry_run = parse_bool(dry_run)
	create_missing = parse_bool(create_missing)
	update_name_fields = parse_bool(update_name_fields)
	fuzzy_threshold = float(fuzzy_threshold)

	if not os.path.exists(csv_path):
		frappe.throw(f"CSV file not found: {csv_path}")

	_ensure_employee_custom_fields()
	rows = _load_rows(csv_path)
	candidates, id_fields = _build_candidates()
	health_provider_name = _ensure_health_insurance_provider(health_insurance_provider, dry_run=dry_run)
	bank_doc_name = _ensure_bank(bank_name, dry_run=dry_run)
	account_type_name = _ensure_bank_account_type(bank_account_type, dry_run=dry_run)

	matched = 0
	updated_employees = 0
	bank_created = 0
	bank_updated = 0
	company_updates = 0
	created_employees = 0
	unmatched = 0
	ambiguous = 0
	conflicts = 0
	results = []
	company_lookup = _build_company_lookup()
	default_company = _resolve_default_company()
	candidate_indexes = {candidate.name: idx for idx, candidate in enumerate(candidates)}

	employee_meta = frappe.get_meta("Employee")
	can_set_health_provider = employee_meta.has_field("health_insurance_provider")
	can_set_health_no = employee_meta.has_field("health_insurance_no")
	can_set_bank_name = employee_meta.has_field("bank_name")
	can_set_bank_ac_no = employee_meta.has_field("bank_ac_no")
	can_set_designation = employee_meta.has_field("designation")
	can_set_first_name = employee_meta.has_field("first_name")
	can_set_last_name = employee_meta.has_field("last_name")
	can_set_employee_name = employee_meta.has_field("employee_name")
	can_set_cell_number = employee_meta.has_field("cell_number")
	father_field = _pick_existing_fields(
		employee_meta,
		["father_name", "custom_father_name", "fathers_name", "custom_fathers_name"],
	)
	national_id_field = _pick_existing_fields(
		employee_meta,
		[
			"custom_national_id_code",
			"national_identity_number",
			"national_id",
			"national_id_no",
			"national_code",
			"custom_national_code",
			"custom_national_id",
		],
	)
	date_of_birth_field = "date_of_birth" if employee_meta.has_field("date_of_birth") else ""
	father_field = father_field[0] if father_field else ""
	national_id_field = national_id_field[0] if national_id_field else ""

	for idx, row in enumerate(rows, start=1):
		insurance_no = normalize_numeric(row.get("شماره بیمه"))
		deposit_no = normalize_numeric(row.get("شماره سپرده"))
		national_code = normalize_national_code(row.get("کد ملی"))
		phone_number = normalize_phone_number(row.get("شماره تماس"))
		father_name = normalize_text(row.get("نام پدر"))
		birth_date_iso = _parse_date_to_iso(row.get("تاریخ تولد"))
		company_from_csv = _resolve_company_name(row.get("شرکت"), company_lookup)
		full_name = normalize_text(
			" ".join(filter(None, [normalize_text(row.get("نام")), normalize_text(row.get("نام خانوادگی"))]))
		)
		first_name = normalize_text(row.get("نام"))
		last_name = normalize_text(row.get("نام خانوادگی"))
		designation_name = _ensure_designation(row.get("عنوان شغلی"), dry_run=dry_run)

		employee_name, match_method, match_score, reason = _resolve_employee(
			row=row, candidates=candidates, threshold=fuzzy_threshold
		)
		if not employee_name:
			if create_missing and (national_code or (full_name and phone_number)):
				if dry_run:
					created_employees += 1
					results.append(
						{
							"row": idx,
							"name": full_name,
							"action": "create_missing",
							"match_method": "create_missing",
							"match_score": 1.0,
							"national_code": national_code,
							"phone_number": phone_number,
							"father_name": father_name,
							"date_of_birth": birth_date_iso,
							"insurance_no": insurance_no,
							"deposit_no": deposit_no,
							"company": company_from_csv or default_company,
							"designation": designation_name,
							"bank_action": "create",
							"message": "employee will be created",
						}
					)
					continue

				created_doc = _create_employee_from_row(
					row=row,
					company_name=company_from_csv or default_company,
					national_id_field=national_id_field,
					father_field=father_field,
					date_of_birth_field=date_of_birth_field,
					designation_name=designation_name,
					dry_run=dry_run,
				)
				if created_doc:
					employee_name = created_doc.name
					match_method = "create_missing"
					match_score = 1.0
					created_employees += 1
					_sync_candidate_cache(
						candidates=candidates,
						candidate_indexes=candidate_indexes,
						employee_doc=created_doc,
						id_fields=id_fields,
					)
				else:
					unmatched += 1
					results.append(
						{
							"row": idx,
							"name": full_name,
							"action": "not_found",
							"score": match_score,
							"message": reason or "unable to create missing employee",
						}
					)
					continue
			else:
				if match_method == "ambiguous":
					ambiguous += 1
				else:
					unmatched += 1
				results.append(
					{
						"row": idx,
						"name": full_name,
						"action": match_method,
						"score": match_score,
						"message": reason,
					}
				)
				continue

		if match_method != "create_missing":
			matched += 1
		employee_doc = frappe.get_doc("Employee", employee_name)
		employee_changed = False
		employee_field_updates = {}

		if update_name_fields:
			if can_set_first_name and first_name:
				if normalize_text(employee_doc.get("first_name")) != first_name:
					employee_doc.set("first_name", first_name)
					employee_field_updates["first_name"] = first_name
					employee_changed = True

			if can_set_last_name and last_name:
				if normalize_text(employee_doc.get("last_name")) != last_name:
					employee_doc.set("last_name", last_name)
					employee_field_updates["last_name"] = last_name
					employee_changed = True

			expected_employee_name = normalize_text(" ".join(filter(None, [first_name, last_name])))
			if can_set_employee_name and expected_employee_name:
				if normalize_text(employee_doc.get("employee_name")) != expected_employee_name:
					employee_doc.set("employee_name", expected_employee_name)
					employee_field_updates["employee_name"] = expected_employee_name
					employee_changed = True

		if can_set_designation and designation_name:
			if employee_doc.get("designation") != designation_name:
				employee_doc.set("designation", designation_name)
				employee_field_updates["designation"] = designation_name
				employee_changed = True

		if can_set_health_provider and health_provider_name:
			if employee_doc.get("health_insurance_provider") != health_provider_name:
				employee_doc.set("health_insurance_provider", health_provider_name)
				employee_field_updates["health_insurance_provider"] = health_provider_name
				employee_changed = True

		if can_set_health_no and insurance_no:
			if normalize_numeric(employee_doc.get("health_insurance_no")) != insurance_no:
				employee_doc.set("health_insurance_no", insurance_no)
				employee_field_updates["health_insurance_no"] = insurance_no
				employee_changed = True

		if father_field and father_name:
			if normalize_text(employee_doc.get(father_field)) != father_name:
				employee_doc.set(father_field, father_name)
				employee_field_updates[father_field] = father_name
				employee_changed = True

		if national_id_field and national_code:
			if normalize_numeric(employee_doc.get(national_id_field)) != national_code:
				employee_doc.set(national_id_field, national_code)
				employee_field_updates[national_id_field] = national_code
				employee_changed = True

		if can_set_cell_number and phone_number:
			if normalize_phone_number(employee_doc.get("cell_number")) != phone_number:
				employee_doc.set("cell_number", phone_number)
				employee_field_updates["cell_number"] = phone_number
				employee_changed = True

		if date_of_birth_field and birth_date_iso:
			current_birth_date = employee_doc.get(date_of_birth_field)
			current_birth_date = str(current_birth_date) if current_birth_date else ""
			if current_birth_date != birth_date_iso:
				employee_doc.set(date_of_birth_field, birth_date_iso)
				employee_field_updates[date_of_birth_field] = birth_date_iso
				employee_changed = True

		if can_set_bank_name and bank_doc_name:
			if employee_doc.get("bank_name") != bank_doc_name:
				employee_doc.set("bank_name", bank_doc_name)
				employee_field_updates["bank_name"] = bank_doc_name
				employee_changed = True

		if can_set_bank_ac_no and deposit_no:
			if normalize_numeric(employee_doc.get("bank_ac_no")) != deposit_no:
				employee_doc.set("bank_ac_no", deposit_no)
				employee_field_updates["bank_ac_no"] = deposit_no
				employee_changed = True

		if company_from_csv and employee_doc.get("company") != company_from_csv:
			employee_doc.set("company", company_from_csv)
			employee_field_updates["company"] = company_from_csv
			company_updates += 1
			employee_changed = True

		if employee_changed and not dry_run:
			frappe.db.set_value("Employee", employee_doc.name, employee_field_updates)
		if employee_changed:
			updated_employees += 1
			_sync_candidate_cache(
				candidates=candidates,
				candidate_indexes=candidate_indexes,
				employee_doc=employee_doc,
				id_fields=id_fields,
			)

		bank_action, bank_message = _upsert_bank_account(
			employee_doc=employee_doc,
			deposit_no=deposit_no,
			bank_name=bank_doc_name,
			bank_account_type=account_type_name,
			dry_run=dry_run,
		)
		if bank_action == "create":
			bank_created += 1
		elif bank_action == "update":
			bank_updated += 1
		elif bank_action == "conflict":
			conflicts += 1

		results.append(
			{
				"row": idx,
				"name": full_name,
				"employee": employee_name,
				"match_method": match_method,
				"match_score": match_score,
				"national_code": national_code,
				"phone_number": phone_number,
				"father_name": father_name,
				"date_of_birth": birth_date_iso,
				"insurance_no": insurance_no,
				"deposit_no": deposit_no,
				"company": company_from_csv,
				"designation": designation_name,
				"bank_action": bank_action,
				"message": bank_message,
			}
		)

	if not dry_run:
		frappe.db.commit()

	return {
		"dry_run": dry_run,
		"csv_path": csv_path,
		"rows": len(rows),
		"matched": matched,
		"unmatched": unmatched,
		"ambiguous": ambiguous,
		"conflicts": conflicts,
		"employee_updates": updated_employees,
		"company_updates": company_updates,
		"bank_created": bank_created,
		"bank_updated": bank_updated,
		"created_employees": created_employees,
		"id_fields_checked": id_fields,
		"father_field": father_field,
		"national_id_field": national_id_field,
		"date_of_birth_field": date_of_birth_field,
		"sample_results": results[:40],
	}


@frappe.whitelist()
def dry_run_employee_insurance_bank_sync(
	csv_path=DEFAULT_CSV_PATH,
	fuzzy_threshold=0.88,
	create_missing=0,
	update_name_fields=1,
):
	return sync_employee_insurance_and_bank_data(
		csv_path=csv_path,
		dry_run=1,
		fuzzy_threshold=fuzzy_threshold,
		create_missing=create_missing,
		update_name_fields=update_name_fields,
	)


@frappe.whitelist()
def apply_employee_insurance_bank_sync(
	csv_path=DEFAULT_CSV_PATH,
	fuzzy_threshold=0.88,
	create_missing=0,
	update_name_fields=1,
):
	return sync_employee_insurance_and_bank_data(
		csv_path=csv_path,
		dry_run=0,
		fuzzy_threshold=fuzzy_threshold,
		create_missing=create_missing,
		update_name_fields=update_name_fields,
	)
