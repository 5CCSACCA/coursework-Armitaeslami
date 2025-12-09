#!/usr/bin/env python3
"""
Firebase Token Helper

This script helps you get a Firebase ID token for API authentication.
You need to provide your Firebase Web API Key and user credentials.

Usage:
    python get_firebase_token.py

Setup:
    1. Get your Firebase Web API Key from:
       Firebase Console → Project Settings → General → Web API Key
    
    2. Create a user in Firebase Console:
       Firebase Console → Authentication → Users → Add User
    
    3. Update the configuration below with your values
"""

import requests
import json
import sys
import os

# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================

# Your Firebase Web API Key (from Firebase Console → Project Settings)
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_API_KEY", "YOUR_WEB_API_KEY_HERE")

# Test user credentials (create this user in Firebase Console → Authentication)
TEST_EMAIL = os.environ.get("FIREBASE_TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.environ.get("FIREBASE_TEST_PASSWORD", "testpassword123")

# ============================================
# DO NOT MODIFY BELOW THIS LINE
# ============================================

FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIREBASE_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"


def sign_in_with_email_password(email: str, password: str, api_key: str) -> dict:
    """
    Sign in with email and password to get Firebase ID token.
    
    Args:
        email: User's email address
        password: User's password
        api_key: Firebase Web API Key
    
    Returns:
        Dictionary with idToken, refreshToken, expiresIn, etc.
    """
    url = f"{FIREBASE_AUTH_URL}?key={api_key}"
    
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        error = response.json().get("error", {})
        raise Exception(f"Firebase Auth Error: {error.get('message', 'Unknown error')}")


def refresh_id_token(refresh_token: str, api_key: str) -> dict:
    """
    Use refresh token to get a new ID token.
    
    Args:
        refresh_token: Firebase refresh token
        api_key: Firebase Web API Key
    
    Returns:
        Dictionary with new id_token, refresh_token, etc.
    """
    url = f"{FIREBASE_REFRESH_URL}?key={api_key}"
    
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        error = response.json().get("error", {})
        raise Exception(f"Token Refresh Error: {error.get('message', 'Unknown error')}")


def create_user(email: str, password: str, api_key: str) -> dict:
    """
    Create a new user account.
    
    Args:
        email: Email for new user
        password: Password for new user
        api_key: Firebase Web API Key
    
    Returns:
        Dictionary with user info and tokens
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        error = response.json().get("error", {})
        raise Exception(f"Create User Error: {error.get('message', 'Unknown error')}")


def print_token_info(token_data: dict):
    """Print token information in a formatted way."""
    print("\n" + "=" * 60)
    print("FIREBASE AUTHENTICATION SUCCESSFUL")
    print("=" * 60)
    
    print("\n📧 User Email:", token_data.get("email", "N/A"))
    print("🆔 Local ID:", token_data.get("localId", "N/A"))
    
    print("\n" + "-" * 60)
    print("🔑 ID TOKEN (use this in Authorization header)")
    print("-" * 60)
    print(token_data.get("idToken", "N/A"))
    
    print("\n" + "-" * 60)
    print("🔄 REFRESH TOKEN (save this to get new tokens)")
    print("-" * 60)
    print(token_data.get("refreshToken", "N/A"))
    
    expires_in = token_data.get("expiresIn", "3600")
    print(f"\n⏱️  Token expires in: {expires_in} seconds ({int(expires_in)//60} minutes)")
    
    print("\n" + "=" * 60)
    print("HOW TO USE")
    print("=" * 60)
    print("""
1. Copy the ID TOKEN above

2. Use it in API requests like this:

   curl -X GET http://localhost:8000/history \\
     -H "Authorization: Bearer <paste-token-here>"

3. Or set it as an environment variable:

   export TOKEN="<paste-token-here>"
   
   curl -X POST http://localhost:8000/detect \\
     -H "Authorization: Bearer $TOKEN" \\
     -F "file=@image.jpg"

4. The token expires in 1 hour. Run this script again to get a new one,
   or use the refresh token with the --refresh option.
""")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Firebase Token Helper")
    parser.add_argument("--email", help="User email (overrides default)")
    parser.add_argument("--password", help="User password (overrides default)")
    parser.add_argument("--api-key", help="Firebase Web API Key (overrides default)")
    parser.add_argument("--refresh", help="Refresh token to use for getting new ID token")
    parser.add_argument("--create", action="store_true", help="Create a new user account")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    # Get configuration
    api_key = args.api_key or FIREBASE_WEB_API_KEY
    email = args.email or TEST_EMAIL
    password = args.password or TEST_PASSWORD
    
    # Validate API key
    if api_key == "YOUR_WEB_API_KEY_HERE":
        print("❌ Error: Please set your Firebase Web API Key!")
        print("\nOptions:")
        print("  1. Edit this script and update FIREBASE_WEB_API_KEY")
        print("  2. Set environment variable: export FIREBASE_API_KEY=your-key")
        print("  3. Pass as argument: --api-key your-key")
        print("\nTo get your API key:")
        print("  Firebase Console → Project Settings → General → Web API Key")
        sys.exit(1)
    
    try:
        if args.refresh:
            # Refresh existing token
            print("🔄 Refreshing token...")
            result = refresh_id_token(args.refresh, api_key)
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("\n🔑 New ID Token:")
                print(result.get("id_token", "N/A"))
                print(f"\n⏱️  Expires in: {result.get('expires_in', '3600')} seconds")
        
        elif args.create:
            # Create new user
            print(f"👤 Creating new user: {email}")
            result = create_user(email, password, api_key)
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print_token_info(result)
        
        else:
            # Sign in
            print(f"🔐 Signing in as: {email}")
            result = sign_in_with_email_password(email, password, api_key)
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print_token_info(result)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        if "EMAIL_NOT_FOUND" in str(e):
            print("\n💡 Tip: The user doesn't exist. Create one with:")
            print(f"   python {sys.argv[0]} --create --email {email} --password {password}")
        
        elif "INVALID_PASSWORD" in str(e):
            print("\n💡 Tip: The password is incorrect. Check your credentials.")
        
        elif "INVALID_API_KEY" in str(e) or "API key not valid" in str(e):
            print("\n💡 Tip: Your API key is invalid. Get it from:")
            print("   Firebase Console → Project Settings → General → Web API Key")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
