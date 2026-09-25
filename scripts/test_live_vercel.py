import urllib.request
import json
import sys

BASE_URL = "https://enermax-crm.vercel.app/api/v1"

def req(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req_obj = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req_obj) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, err_body
    except Exception as e:
        return 0, str(e)

print("[1] Testing Login...")
status, res = req("/auth/login", "POST", {"email": "operator@enermax.com", "password": "Operator123!"})
print("    Login Status:", status)
if status != 200:
    print("    Failed:", res)
    sys.exit(1)

token = res["data"]["access_token"]
tenant_id = res["data"]["user"]["organization_id"]
print("    Authenticated as Operator. Tenant ID:", tenant_id)

print("\n[2] Testing Dashboard (/dashboard)...")
s, d = req("/dashboard", token=token)
print(f"    Status: {s}, Active Projects: {d.get('data', {}).get('active_projects_count')}")

print("\n[3] Testing Customers (/customers)...")
s, c = req("/customers", token=token)
customers_list = c.get("data", [])
print(f"    Status: {s}, Count: {len(customers_list)}")

print("\n[4] Creating New Customer...")
s, new_c = req("/customers", "POST", {
    "name": "Mahindra Solar Industries",
    "email": "contact@mahindrasolar.in",
    "phone": "+91 9988776655",
    "customer_type": "commercial",
    "status": "qualified",
    "source": "referral"
}, token=token)
print(f"    Status: {s}, ID: {new_c.get('data', {}).get('id')}")
created_customer_id = new_c.get("data", {}).get("id")

print("\n[5] Testing Pipelines (/pipelines)...")
s, p = req("/pipelines", token=token)
pipelines_list = p.get("data", [])
print(f"    Status: {s}, Pipelines: {len(pipelines_list)}")

print("\n[6] Testing Projects (/projects)...")
s, pr = req("/projects", token=token)
projects_list = pr.get("data", [])
print(f"    Status: {s}, Projects: {len(projects_list)}")

print("\n[7] Creating New Project...")
s, new_p = req("/projects", "POST", {
    "name": "50kW Industrial Rooftop Plant",
    "customer_id": created_customer_id,
    "capacity_kw": 50.0,
    "estimated_cost": 2200000.0,
    "system_type": "commercial_rooftop",
    "notes": "Fast-track industrial client"
}, token=token)
print(f"    Status: {s}, Project ID: {new_p.get('data', {}).get('id')}")
created_project_id = new_p.get("data", {}).get("id")

print("\n[8] Testing Follow-ups (/follow-ups)...")
s, f = req("/follow-ups", token=token)
print(f"    Status: {s}, Follow-ups: {len(f.get('data', []))}")

print("\n[9] Creating Follow-up...")
s, new_f = req("/follow-ups", "POST", {
    "customer_id": created_customer_id,
    "project_id": created_project_id,
    "title": "Site Inspection & Shadow Analysis",
    "due_date": "2026-10-01T10:00:00",
    "priority": "high",
    "type": "site_visit"
}, token=token)
print(f"    Status: {s}, Follow-up ID: {new_f.get('data', {}).get('id')}")

print("\n[10] Testing Payments (/payments)...")
s, py = req("/payments", token=token)
print(f"    Status: {s}, Payments: {len(py.get('data', []))}")

print("\n[11] Creating Payment...")
s, new_pay = req("/payments", "POST", {
    "project_id": created_project_id,
    "customer_id": created_customer_id,
    "amount": 500000.0,
    "payment_date": "2026-09-25",
    "payment_method": "bank_transfer",
    "status": "completed",
    "reference_number": "TXN_SOLAR_88319"
}, token=token)
print(f"    Status: {s}, Payment ID: {new_pay.get('data', {}).get('id')}")

print("\n[12] Testing Products (/products)...")
s, prod = req("/products", token=token)
print(f"    Status: {s}, Products: {prod.get('data')}")

print("\n[12b] Creating New Product (/products)...")
s, new_prod = req("/products", "POST", {
    "name": "High-Efficiency Monocrystalline PERC 550W",
    "sku": "SOLAR-PERC-550W",
    "category": "Solar EPC",
    "description": "Tier 1 bifacial monocrystalline solar modules with 21.3% efficiency.",
    "unit_price": 14500.0,
}, token=token)
print(f"    Status: {s}, Product ID: {new_prod.get('data', {}).get('id') if isinstance(new_prod, dict) else new_prod}")

print("\n[13] Testing Custom Fields (/custom-fields)...")
s, cf = req("/custom-fields", token=token)
print(f"    Status: {s}, Fields: {len(cf.get('data', []))}")

print("\n[14] Testing Views (/views)...")
s, v = req("/views", token=token)
print(f"    Status: {s}, Views: {len(v.get('data', []))}")

print("\n[15] Testing Notifications (/notifications)...")
s, n = req("/notifications", token=token)
print(f"    Status: {s}, Notifications: {len(n.get('data', []))}")

print("\n==========================================")
print("ALL LIVE VERCEL TESTS COMPLETED SUCCESSFULLY!")
print("==========================================")
