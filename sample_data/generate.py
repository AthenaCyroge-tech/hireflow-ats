"""Generates sample_data/applicants_400.csv (fictional people) for testing bulk import."""
import csv, random
from datetime import date, timedelta
from pathlib import Path

random.seed(7)
FIRST = "Aarav Priya Ishaan Ananya Kabir Meera Rohan Zoya Vihaan Diya Arjun Sara Neha Rahul Kavya Aditya Nikhil Sneha Varun Tanya Harsh Pooja Manav Ritika Dev Isha Yash Aditi Karan Lakshmi Faisal Anjali Gaurav Nandini Sahil Bhavya Omkar Jiya Reyansh".split()
LAST = "Sharma Nair Mehta Rao Das Iyer Verma Khan Reddy Menon Pillai Thomas Gupta Patel Joshi Kumar Singh Bose Kulkarni Shetty Naidu Chopra Banerjee Desai Kapoor Mishra Pandey Jain Nambiar Varghese".split()
ROLES = {
    "Python Developer": ["Python", "Django", "Flask", "SQL", "REST APIs"],
    "Frontend Developer": ["React", "TypeScript", "CSS", "JavaScript", "Tailwind"],
    "Backend Developer": ["Java", "Spring Boot", "Node.js", "PostgreSQL", "Docker"],
    "Full Stack Developer": ["React", "Node.js", "PostgreSQL", "MongoDB", "Git"],
    "Data Analyst": ["SQL", "Excel", "Power BI", "Tableau", "Python"],
    "UI/UX Designer": ["Figma", "Wireframing", "User Research", "Prototyping"],
    "Product Management Intern": ["User Research", "SQL", "Figma", "Communication", "Analytics"],
}
STAGES = ["Applied"] * 45 + ["Screening"] * 25 + ["Interview"] * 14 + ["Offer"] * 5 + ["Hired"] * 4 + ["Rejected"] * 7
SOURCES = ["Career site", "LinkedIn", "Referral", "Job board", "Campus", "Other"]

rows, seen = [], set()
today = date.today()
while len(rows) < 400:
    f, l = random.choice(FIRST), random.choice(LAST)
    email = f"{f}.{l}{len(rows) + 1}@example.com".lower()
    if email in seen:
        continue
    seen.add(email)
    role = random.choice(list(ROLES))
    rows.append(dict(
        name=f"{f} {l}", email=email, phone=f"+91 9{random.randint(100000000, 999999999)}", role=role,
        skills=", ".join(random.sample(ROLES[role], 3)), experience=random.choice([0, 0, 1, 1, 2, 2, 3, 4, 5, 6]),
        source=random.choice(SOURCES), stage=random.choice(STAGES),
        applied_date=(today - timedelta(days=random.randint(0, 45))).isoformat(), notes=""))

out = Path(__file__).with_name("applicants_400.csv")
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print("wrote", out, len(rows))
