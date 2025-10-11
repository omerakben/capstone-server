"""
Create Firebase credentials JSON file from environment variables at startup.

This script runs before Django starts to create a temporary Firebase service account
JSON file from individual environment variables. This avoids multiline string issues
with the private key in environment variables.
"""

import json
import os
import sys

def create_firebase_credentials():
    """Create Firebase credentials JSON from environment variables."""

    # Check if running in a mode that needs Firebase
    if os.getenv("DEMO_MODE", "").lower() == "true":
        print("Demo mode enabled, skipping Firebase credentials creation")
        return

    # Check if credentials file already exists
    creds_path = os.getenv("FIREBASE_CREDENTIALS_FILE", "")
    if creds_path and os.path.exists(creds_path):
        print(f"Firebase credentials file already exists at {creds_path}")
        return

    # Get all Firebase environment variables
    firebase_config = {
        "type": os.getenv("FIREBASE_TYPE", "service_account"),
        "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", ""),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
        "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
        "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.getenv(
            "FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
            "https://www.googleapis.com/oauth2/v1/certs"
        ),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL", ""),
    }

    # Check if we have the minimum required fields
    if not firebase_config["project_id"] or not firebase_config["private_key"]:
        print("Firebase environment variables not configured, skipping credentials creation")
        return

    # Fix private key format - ensure it has proper newlines
    private_key = firebase_config["private_key"]
    # Replace literal \n with actual newlines if needed
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")
    firebase_config["private_key"] = private_key

    # Create credentials file in /tmp (Railway's writable directory)
    temp_creds_path = "/tmp/firebase-credentials.json"

    try:
        with open(temp_creds_path, 'w') as f:
            json.dump(firebase_config, f, indent=2)

        # Set environment variable for Django to use
        os.environ["FIREBASE_CREDENTIALS_FILE"] = temp_creds_path

        print(f"✅ Firebase credentials file created at {temp_creds_path}")

    except Exception as e:
        print(f"❌ Failed to create Firebase credentials file: {e}", file=sys.stderr)
        # Don't fail the startup - continue without Firebase if needed
        return

if __name__ == "__main__":
    create_firebase_credentials()
