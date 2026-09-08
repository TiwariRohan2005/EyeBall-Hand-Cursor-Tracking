import sys
from modules.auth.storage import UserStorage
from library_app.database.db import DatabaseManager
from library_app.database.repository import LibraryRepository

def print_help():
    print("""
==== TrueEyeball User Management ====
Usage: python manage_users.py <command> [args]
Commands:
    list                    - List all registered users and capacity limits
    rename <old> <new>      - Rename a registered user
    revoke <name>           - Delete a user profile (revoke access)
=====================================
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()
    storage = UserStorage()
    
    db_mgr = DatabaseManager()
    db_mgr.init_db()
    repo = LibraryRepository(db_mgr)

    if command == "list":
        users = storage.get_all_users()
        limits = repo.get_role_counts()
        
        print("\n--------------------------------")
        print("USER CAPACITY")
        print("--------------------------------")
        print(f"Owner: {limits.get('OWNER', 0)} / 1")
        print(f"Staff: {limits.get('STAFF', 0)} / 10")
        print("--------------------------------\n")
        
        if not users:
            print("No users registered in Secure Enclave.")
        else:
            db_users = repo.list_users()
            db_user_map = {u['username']: u for u in db_users}
            
            print(f"{'Username':<15} | {'Role':<10} | {'Status':<10} | {'Joined'}")
            print("-" * 55)
            for uid in users.keys():
                u_info = db_user_map.get(uid, {})
                role = u_info.get('role', 'UNKNOWN')
                status = "ACTIVE" if u_info.get('active', 1) else "DEACTIVATED"
                created = u_info.get('created_at', 'Unknown Timestamp')
                print(f"{uid:<15} | {role:<10} | {status:<10} | {created}")
            print()

    elif command == "rename":
        if len(sys.argv) != 4:
            print("Usage: python manage_users.py rename <old_name> <new_name>")
            return
        
        old_name = sys.argv[2]
        new_name = sys.argv[3]
        if storage.rename_user(old_name, new_name):
            print(f"[+] Renamed '{old_name}' to '{new_name}' in storage.")
            print("[!] Note: You must manually migrate Database ownership rows for consistency.")
        else:
            print(f"[-] Could not rename. Make sure '{old_name}' exists and '{new_name}' isn't already taken.")

    elif command == "revoke":
        if len(sys.argv) != 3:
            print("Usage: python manage_users.py revoke <name>")
            return
            
        name = sys.argv[2]
        if storage.delete_user(name):
            print(f"[+] Access revoked for '{name}'. Biometric Profile deleted.")
            # Also deactivate in DB so they don't count towards staff limits
            u = repo.get_user_by_username(name)
            if u:
                with repo.db.get_connection() as conn:
                    conn.execute("UPDATE users SET active = 0 WHERE username = ?", (name,))
                print(f"[+] User '{name}' safely deactivated in Backend DB.")
        else:
            print(f"[-] Could not find user '{name}' in biometric vault.")

    else:
        print_help()

if __name__ == "__main__":
    main()
