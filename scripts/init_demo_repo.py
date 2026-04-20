#!/usr/bin/env python3
"""Initialize demo_repo as a git repository with realistic commit history."""

import subprocess
import os

REPO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_repo")


def run(cmd, cwd=REPO_DIR):
    subprocess.run(cmd, shell=True, cwd=cwd, check=True, capture_output=True)


def commit(msg, date):
    env_date = f'GIT_AUTHOR_DATE="{date}" GIT_COMMITTER_DATE="{date}"'
    run(f'{env_date} git commit --allow-empty -m "{msg}"')


def main():
    # Init repo
    run("git init")
    run('git config user.email "dev@example.com"')
    run('git config user.name "Demo Developer"')

    # Initial commit - add all files
    run("git add -A")
    run('GIT_AUTHOR_DATE="2024-06-01T10:00:00" GIT_COMMITTER_DATE="2024-06-01T10:00:00" '
        'git commit -m "Initial commit: e-commerce backend with order, payment, inventory services"')

    # Simulate realistic commit history
    commits = [
        ("2024-06-15T14:30:00", "Add currency validation to payment processing"),
        ("2024-07-02T09:15:00", "Fix stock deduction race condition in inventory service"),
        ("2024-08-14T16:45:00", "Add error handling for payment gateway timeouts"),
        ("2024-09-01T11:00:00", "Refactor order cancellation to handle paid orders"),
        ("2024-09-30T13:20:00", "Fix validation bypass allowing negative order amounts"),
        ("2024-10-15T10:30:00", "Add refund endpoint with basic validation"),
        ("2024-11-08T15:00:00", "Add optimistic locking to inventory deduction"),
        ("2024-12-01T09:00:00", "Improve error messages in validation utilities"),
        ("2025-01-22T14:30:00", "Make refund call async in order cancellation flow"),
        ("2025-02-10T11:15:00", "Add payment status check endpoint"),
        ("2025-03-15T16:00:00", "Refactor refund validation logic for multi-currency support"),
    ]

    for date, msg in commits:
        commit(msg, date)

    print(f"Demo repo initialized at {REPO_DIR}")
    print(f"Total commits: {len(commits) + 1}")

    # Show log
    result = subprocess.run(
        "git log --oneline", shell=True, cwd=REPO_DIR, capture_output=True, text=True
    )
    print(result.stdout)


if __name__ == "__main__":
    main()
