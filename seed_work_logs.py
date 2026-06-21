import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Please set SUPABASE_URL and SUPABASE_KEY in .env")
    exit(1)

client_key = SUPABASE_SERVICE_ROLE_KEY if SUPABASE_SERVICE_ROLE_KEY else SUPABASE_KEY
supabase: Client = create_client(SUPABASE_URL, client_key)

# Fetch all profiles
try:
    profiles_res = supabase.table('profiles').select('*').execute()
    profiles = profiles_res.data
except Exception as e:
    print(f"Error fetching profiles: {e}")
    exit(1)

if not profiles:
    print("No profiles found to seed work logs for. Run seed_users.py first.")
    exit(1)

print(f"Found {len(profiles)} profiles. Generating 150 random work logs...")

work_descriptions = {
    "cipl": [
        "Reconfigured switch routing and VLAN configurations on site.",
        "Resolved internet drop issues in main admin office.",
        "Installed new fiber patch panels in server room.",
        "Monitored network traffic spikes and mitigated DDoS threat.",
        "Maintained rack cabling and cleaned up server layout.",
        "Replaced faulty ethernet lines on second floor.",
        "Assisted team with firewall rule updates.",
        "Conducted security audit of external-facing routers.",
        "Updated server firmware and completed patch cycle."
    ],
    "standard": [
        "Drafted monthly performance report and coordinated with divisions.",
        "Attended regional committee sync meeting at Head Office.",
        "Reviewed and updated internal process manuals.",
        "Conducted training session for new interns regarding portal usage.",
        "Managed database log rotation and freed up storage.",
        "Prepared presentation slides for executive board meet.",
        "Analyzed operational cost metrics for Q2.",
        "Followed up with branch managers regarding pending approvals."
    ]
}

logs_to_insert = []
start_date = datetime.now() - timedelta(days=45)

for _ in range(150):
    profile = random.choice(profiles)
    
    # Generate random timestamp within the last 45 days
    random_days = random.randint(0, 45)
    random_hours = random.randint(8, 18)
    random_minutes = random.randint(0, 59)
    log_time = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
    
    # Check type of work options
    if profile.get('is_cipl'):
        work_type = random.choice(["NETWORK", "SERVICE", "MAINTENANCE", "SUPPORT", "OTHER"])
        desc = random.choice(work_descriptions["cipl"])
    else:
        work_type = random.choice(["HO", "RBCSC", "SRO"])
        desc = random.choice(work_descriptions["standard"])
        
    hours = random.choice([1.0, 1.5, 2.0, 3.0, 4.0, 5.5, 6.0, 8.0, 8.5])
    status = random.choice(["approved", "pending", "rejected", "approved", "approved"]) # weight towards approved/pending
    
    logs_to_insert.append({
        "user_id": profile["id"],
        "timestamp": log_time.isoformat(),
        "work_type": work_type,
        "description": f"{desc} - {random.randint(100, 999)}",
        "hours": hours,
        "status": status
    })

print("Inserting work logs...")
try:
    # Insert in batches of 50
    for i in range(0, len(logs_to_insert), 50):
        batch = logs_to_insert[i:i+50]
        supabase.table('work_logs').insert(batch).execute()
        print(f"Inserted batch {i//50 + 1}/3")
    print("Successfully seeded 150 work logs!")
except Exception as e:
    print(f"Error seeding logs: {e}")
