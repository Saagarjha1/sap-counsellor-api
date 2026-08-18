import os
import json
import gspread
from flask import Flask, jsonify, request
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# File path to Render secret file or local fallback
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/etc/secrets/service_account.json')

def get_gspread_client():
    """Loads and repairs service account credentials to authenticate gspread."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found at {SERVICE_ACCOUNT_FILE}")
    
    with open(SERVICE_ACCOUNT_FILE, 'r') as f:
        key_dict = json.load(f)

    # Clean space artifacts and fix newline escaping in private key
    if "private_key" in key_dict and isinstance(key_dict["private_key"], str):
        key_dict["private_key"] = key_dict["private_key"].replace(" ", "").replace("\\n", "\n")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(key_dict, scopes=scopes)
    return gspread.authorize(credentials)

# Initialize Google Sheets Client
try:
    gc = get_gspread_client()
    print(" Successfully authenticated with Google Sheets API.")
except Exception as e:
    print(f"❌ Failed to initialize Google authentication: {e}")
    gc = None


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "online",
        "message": "Service Account API is running."
    }), 200


@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint to check if Google Sheets connection is healthy."""
    if gc is None:
        return jsonify({"status": "error", "message": "Google authentication failed"}), 500
    return jsonify({"status": "healthy", "google_auth": "connected"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
