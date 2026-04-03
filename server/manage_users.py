#!/usr/bin/env python
"""
User management CLI - chay local tren may prod
Usage:
    python manage_users.py add <username> <password> <customer> <tasks>
    python manage_users.py list
    python manage_users.py delete <username>
    python manage_users.py deactivate <username>
    
Example:
    python manage_users.py add admin 123456 HADDAD PHOTO8,PDF_TO_EXCEL,COSTING,DELEGATE
    python manage_users.py add user1 123456 LTD PHOTO8,PDF_TO_EXCEL
    python manage_users.py list
"""
import sys
import argparse
from pathlib import Path
from passlib.hash import bcrypt

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))

from config import JOBS_DIR
from repositories.user_repository import UserRepository


def create_user(username: str, password: str, customer: str, tasks: str):
    repo = UserRepository(JOBS_DIR / "jobs.sqlite")
    
    task_list = [t.strip() for t in tasks.split(",") if t.strip()]
    password_hash = bcrypt.hash(password)
    
    try:
        repo.create_user(username, password_hash, customer, task_list)
        print(f"Created user: {username} | customer: {customer} | tasks: {task_list}")
    except Exception as e:
        print(f"Error: {e}")


def list_users():
    repo = UserRepository(JOBS_DIR / "jobs.sqlite")
    users = repo.list_users()
    
    if not users:
        print("No users found")
        return
    
    print(f"\n{'Username':<20} {'Customer':<10} {'Allowed Tasks':<40} {'Active':<8}")
    print("-" * 80)
    for u in users:
        tasks = ", ".join(u.get("allowed_tasks", []))
        active = "Yes" if u.get("is_active") else "No"
        print(f"{u['username']:<20} {u['customer']:<10} {tasks:<40} {active:<8}")


def delete_user(username: str):
    repo = UserRepository(JOBS_DIR / "jobs.sqlite")
    repo.delete_user(username)
    print(f"Deleted user: {username}")


def deactivate_user(username: str):
    repo = UserRepository(JOBS_DIR / "jobs.sqlite")
    from repositories.user_repository import now_iso
    with repo._conn() as c:
        c.execute("UPDATE users SET is_active=0, updated_at=? WHERE username=?", (now_iso(), username))
        c.commit()
    print(f"Deactivated user: {username}")


def activate_user(username: str):
    repo = UserRepository(JOBS_DIR / "jobs.sqlite")
    from repositories.user_repository import now_iso
    with repo._conn() as c:
        c.execute("UPDATE users SET is_active=1, updated_at=? WHERE username=?", (now_iso(), username))
        c.commit()
    print(f"Activated user: {username}")


def main():
    parser = argparse.ArgumentParser(description="User management CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    parser_add = subparsers.add_parser("add", help="Add new user")
    parser_add.add_argument("username")
    parser_add.add_argument("password")
    parser_add.add_argument("customer")
    parser_add.add_argument("tasks", help="Comma-separated: PHOTO8,PDF_TO_EXCEL,COSTING,DELEGATE")
    
    subparsers.add_parser("list", help="List all users")
    
    parser_delete = subparsers.add_parser("delete", help="Delete user")
    parser_delete.add_argument("username")
    
    parser_deactivate = subparsers.add_parser("deactivate", help="Deactivate user")
    parser_deactivate.add_argument("username")
    
    parser_activate = subparsers.add_parser("activate", help="Activate user")
    parser_activate.add_argument("username")
    
    args = parser.parse_args()
    
    if args.command == "add":
        create_user(args.username, args.password, args.customer, args.tasks)
    elif args.command == "list":
        list_users()
    elif args.command == "delete":
        delete_user(args.username)
    elif args.command == "deactivate":
        deactivate_user(args.username)
    elif args.command == "activate":
        activate_user(args.username)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()