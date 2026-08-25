import sys
import traceback
try:
    import frappe
    frappe.init(site='erpyar.ir')
    frappe.connect()
    
    import os
    
    rt_dir = '/home/frappe/frappe-bench/apps/hrms/hrms/hr/doctype/rest_time'
    print("Rest Time dir exists:", os.path.isdir(rt_dir), flush=True)
    rt_json = os.path.join(rt_dir, 'rest_time.json')
    print("Rest Time json exists:", os.path.exists(rt_json), flush=True)
    
    # Check if doctype is already in the database
    exists = frappe.db.exists('DocType', 'Rest Time')
    print("Rest Time in DB:", exists, flush=True)
    
    exists2 = frappe.db.exists('DocType', 'Rest Time Assignment')
    print("Rest Time Assignment in DB:", exists2, flush=True)
    
    if not exists:
        print("Creating Rest Time doctype from file...", flush=True)
        with open(rt_json) as f:
            import json
            data = json.load(f)
        doc = frappe.get_doc(data)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Rest Time doctype created!", flush=True)
    
    rta_dir = '/home/frappe/frappe-bench/apps/hrms/hrms/hr/doctype/rest_time_assignment'
    rta_json = os.path.join(rta_dir, 'rest_time_assignment.json')
    if not exists2:
        print("Creating Rest Time Assignment doctype from file...", flush=True)
        with open(rta_json) as f:
            data = json.load(f)
        doc = frappe.get_doc(data)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Rest Time Assignment doctype created!", flush=True)
    
    frappe.destroy()
except Exception as e:
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
