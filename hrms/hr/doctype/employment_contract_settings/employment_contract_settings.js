frappe.ui.form.on('Employment Contract Settings', {
	refresh(frm) {
		frm.add_custom_button(__('تنظیمات قرارداد را به‌روزرسانی کنید و ذخیره بزنید.'), () => {}, __('راهنما'))
	}
})
