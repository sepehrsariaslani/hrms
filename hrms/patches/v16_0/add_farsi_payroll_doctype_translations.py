import frappe


FA_DOCTYPE_TRANSLATIONS = {
	"Iran Payroll Settings": "تنظیمات حقوق و دستمزد ایران",
	"Iran Seniority Table": "جدول پایه سنوات",
	"Gratuity Rule": "جدول مزایای پایان خدمت",
	"Overtime Slip": "فیش اضافه کاری",
	"Overtime Type": "نوع اضافه کاری",
}


def execute():
	for source_text, translated_text in FA_DOCTYPE_TRANSLATIONS.items():
		existing = frappe.get_all(
			"Translation",
			filters={"language": "fa", "source_text": source_text},
			fields=["name", "translated_text"],
			limit=1,
		)
		if existing:
			row = existing[0]
			if row.translated_text != translated_text:
				frappe.db.set_value(
					"Translation",
					row.name,
					"translated_text",
					translated_text,
					update_modified=False,
				)
			continue

		doc = frappe.new_doc("Translation")
		doc.language = "fa"
		doc.source_text = source_text
		doc.translated_text = translated_text
		doc.insert(ignore_permissions=True)
