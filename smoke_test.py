import warnings
warnings.filterwarnings("ignore")
from app import create_app
from config import Config

app = create_app(Config)

def login(client, email, password="password123"):
    return client.post("/auth/login", data={"email": email, "password": password},
                       follow_redirects=True)

tests = []

with app.test_client() as c:
    r = login(c, "alex@student.com")
    tests.append(("student login", r.status_code))
    for path in ["/student/dashboard", "/student/profile", "/student/skills", "/student/portfolio",
                 "/student/certificates", "/student/assessments", "/student/applications",
                 "/student/earnings", "/student/wishlist", "/student/resume/view",
                 "/student/resume/print", "/projects/", "/projects/students", "/projects/1",
                 "/projects/students/1", "/notifications/", "/messages/", "/messages/2"]:
        resp = c.get(path, follow_redirects=True)
        tests.append((path, resp.status_code))

with app.test_client() as c:
    r = login(c, "techcorp@client.com")
    tests.append(("client login", r.status_code))
    for path in ["/client/dashboard", "/client/profile", "/client/projects/post", "/client/projects",
                 "/client/proposals/all", "/client/hired", "/client/payments"]:
        resp = c.get(path, follow_redirects=True)
        tests.append((path, resp.status_code))

with app.test_client() as c:
    r = login(c, "admin@skillbridge.com", "admin123")
    tests.append(("admin login", r.status_code))
    for path in ["/admin/", "/admin/users", "/admin/students", "/admin/clients",
                 "/admin/projects", "/admin/proposals", "/admin/hired",
                 "/admin/skills", "/admin/categories", "/admin/certificates",
                 "/admin/reviews", "/admin/payments", "/admin/withdrawals",
                 "/admin/notifications", "/admin/reports",
                 "/assessments/admin"]:
        resp = c.get(path, follow_redirects=True)
        tests.append((path, resp.status_code))

print("RESULTS:")
fails = 0
for name, code in tests:
    mark = "OK " if code in (200, 302) else "FAIL"
    if code not in (200, 302):
        fails += 1
    print(f"  {mark} {name:40s} -> {code}")
print(f"\nTotal: {len(tests)}, Failures: {fails}")
