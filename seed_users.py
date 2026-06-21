import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Please set SUPABASE_URL and SUPABASE_KEY in .env")
    exit(1)

# Use service role key if available to bypass rate limits
client_key = SUPABASE_SERVICE_ROLE_KEY if SUPABASE_SERVICE_ROLE_KEY else SUPABASE_KEY
supabase: Client = create_client(SUPABASE_URL, client_key)

# Wait for Supabase trigger to create the profile row, to avoid race conditions.
def wait_and_update_profile(user_id, is_admin, is_employee, is_cipl, retries=5):
    for i in range(retries):
        try:
            # Check if profile exists
            profile = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
            if profile.data:
                # Update profile
                supabase.table('profiles').update({
                    'is_admin': is_admin,
                    'is_employee': is_employee,
                    'is_cipl': is_cipl
                }).eq('id', user_id).execute()
                return True
        except Exception as e:
            pass
        time.sleep(1)
    print(f"Failed to update profile for {user_id}")
    return False

users_data = [
    {"username": "00507733", "name": "HEMA", "type": "EMPLOYEE", "password": "hema123"},
    {"username": "00036049", "name": "PRIYADARSHINI", "type": "ADMIN & EMPLOYEE", "password": "priya123"},
    {"username": "00081675", "name": "MALAMARUGAN", "type": "ADMIN", "password": "mala123"},
    {"username": "00040032", "name": "PRASANNA KUMAR", "type": "ADMIN", "password": "prasanna123"},
    {"username": "00511175", "name": "MUNNAM PAVAN", "type": "EMPLOYEE", "password": "pavan123"},
    {"username": "00503143", "name": "BUSHRA", "type": "EMPLOYEE", "password": "bushra123"},
    {"username": "00508558", "name": "NIVETHA", "type": "EMPLOYEE", "password": "nivetha123"},
    {"username": "12345678", "name": "DC ENGG NETW", "type": "CIPL", "password": "CIPL123"},
    {"username": "87654321", "name": "DC ENGG SERV", "type": "CIPL", "password": "CIPL321"}
]

print("Starting to seed users...")

for u in users_data:
    # We use a standard domain to pass Supabase validation
    email = f"{u['username']}@worklog.com"
    
    # Determine roles
    role_str = u['type']
    is_admin = "ADMIN" in role_str
    is_employee = "EMPLOYEE" in role_str
    is_cipl = "CIPL" in role_str
    
    try:
        if SUPABASE_SERVICE_ROLE_KEY:
            # Use admin API to bypass rate limits and email confirmation
            res = supabase.auth.admin.create_user({
                "email": email, 
                "password": u['password'],
                "email_confirm": True,
                "user_metadata": {
                    "name": u['name'],
                    "username": u['username']
                }
            })
            user_id = res.user.id
        else:
            # Create user in standard Auth
            res = supabase.auth.sign_up({
                "email": email, 
                "password": u['password'],
                "options": {
                    "data": {
                        "name": u['name'],
                        "username": u['username']
                    }
                }
            })
            user_id = res.user.id
            
        print(f"Created Auth User: {u['username']} ({u['name']})")
        
        # Update the roles in public.profiles table created by the trigger
        wait_and_update_profile(user_id, is_admin, is_employee, is_cipl)
        print(f"  -> Updated roles: Admin={is_admin}, Emp={is_employee}, CIPL={is_cipl}")
        
    except Exception as e:
        print(f"Error creating user {u['username']}: {str(e)}")

print("\nSeeding complete!")
print("NOTE: Users log in using their 'USERNAME@worklog.com' as the email address, and their SECRET CODE as the password.")
