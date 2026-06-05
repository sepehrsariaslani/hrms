frappe.pages["organizational-chart"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Organizational Chart"),
		single_column: true,
	});

	$(wrapper).bind("show", () => {
		frappe.require(["hrms.bundle.js", "hierarchy-chart.bundle.js"], () => {
			let organizational_chart;
			let method = "hrms.hr.page.organizational_chart.organizational_chart.get_children";
			const hrms_ns = window.hrms || {};

			const chart_cls = frappe.is_mobile() ? hrms_ns.HierarchyChartMobile : hrms_ns.HierarchyChart;
			if (!chart_cls) {
				frappe.msgprint(__("HRMS chart assets are not ready yet. Please refresh the page."));
				return;
			}
			organizational_chart = new chart_cls("Employee", wrapper, method);

			frappe.breadcrumbs.add("HR");
			organizational_chart.show();
		});
	});
};
