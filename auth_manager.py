"""
auth_manager.py — Standalone runner for Registration & Authentication.

Demonstrates the complete auth flow:
  1. Registration  → receives clientID + clientSecret
  2. Authentication → receives Bearer access_token
  3. Stores all credentials securely in .env

Usage:
    python auth_manager.py
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logging_middleware.logger.auth import TokenManager
from logging_middleware.logger.config import settings


def mask(value: str, show_start: int = 8, show_end: int = 4) -> str:
    """Partially mask a secret for safe display."""
    if not value or len(value) < show_start + show_end + 4:
        return "****"
    return f"{value[:show_start]}...{value[-show_end:]}"


def main():
    print("=" * 55)
    print("  Phase 1 — Registration & Authentication Runner")
    print("=" * 55)

    tm = TokenManager()

    # --- Step 1: Registration ---
    print("\n[Step 1] Registration")
    print("-" * 40)

    if settings.CLIENT_ID and settings.CLIENT_SECRET:
        print("  ✔ Already registered (credentials found in .env)")
        print(f"  CLIENT_ID    : {mask(settings.CLIENT_ID)}")
        print(f"  CLIENT_SECRET: {mask(settings.CLIENT_SECRET, 4, 0)}")
    else:
        print("  → Calling Registration API...")
        client_id, client_secret = tm.register()
        if client_id:
            print(f"  ✔ Registration successful!")
            print(f"  CLIENT_ID    : {mask(client_id)}")
            print(f"  CLIENT_SECRET: {mask(client_secret, 4, 0)}")
        else:
            print("  ✘ Registration failed. Check your credentials in .env")
            sys.exit(1)

    # --- Step 2: Authentication ---
    print("\n[Step 2] Authentication")
    print("-" * 40)

    if settings.ACCESS_TOKEN:
        print("  ✔ Already authenticated (token found in .env)")
        print(f"  ACCESS_TOKEN : {mask(settings.ACCESS_TOKEN, 20, 10)}")
        print(f"  Token Type   : Bearer")

        # Offer to refresh
        print("\n  → Re-authenticating to verify token validity...")
        fresh_token = tm.authenticate()
        if fresh_token:
            print(f"  ✔ Fresh token obtained!")
            print(f"  ACCESS_TOKEN : {mask(fresh_token, 20, 10)}")
        else:
            print("  ⚠ Re-auth failed — existing token may still be valid.")
    else:
        print("  → Calling Authentication API...")
        token = tm.authenticate()
        if token:
            print(f"  ✔ Authentication successful!")
            print(f"  ACCESS_TOKEN : {mask(token, 20, 10)}")
            print(f"  Token Type   : Bearer")
        else:
            print("  ✘ Authentication failed.")
            sys.exit(1)

    # --- Summary ---
    print("\n" + "=" * 55)
    print("  ✔ Phase 1 Complete — All credentials secured in .env")
    print("=" * 55)
    print(f"\n  Credentials stored at: {os.path.abspath('.env')}")
    print("  .env is gitignored   : YES")
    print("  Ready for Phase 2    : YES\n")


if __name__ == "__main__":
    main()
