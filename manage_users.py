import sys
from modules.auth.storage import UserStorage

def print_help():
    print("""
==== TrueEyeball User Management ====
Usage: python manage_users.py <command> [args]
Commands:
    list                    - List all registered users
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

    if command == "list":
        users = storage.get_all_users()
        if not users:
            print("No users registered.")
        else:
            print("\nRegistered Users:")
            for uid in users.keys():
                print(f"  - {uid}")
            print()

    elif command == "rename":
        if len(sys.argv) != 4:
            print("Usage: python manage_users.py rename <old_name> <new_name>")
            return
        
        old_name = sys.argv[2]
        new_name = sys.argv[3]
        if storage.rename_user(old_name, new_name):
            print(f"[+] Renamed '{old_name}' to '{new_name}'.")
        else:
            print(f"[-] Could not rename. Make sure '{old_name}' exists and '{new_name}' isn't already taken.")

    elif command == "revoke":
        if len(sys.argv) != 3:
            print("Usage: python manage_users.py revoke <name>")
            return
            
        name = sys.argv[2]
        if storage.delete_user(name):
            print(f"[+] Access revoked for '{name}'. Profile deleted.")
        else:
            print(f"[-] Could not find user '{name}'.")

    else:
        print_help()

if __name__ == "__main__":
    main()
