from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import re
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
# Enable CORS so external frontends (React, Webflow, Vercel, Netlify) can call this API
CORS(app)

# ==================== GOOGLE SHEETS SETUP ====================
SHEET_ID = "1BNItqKaexdv5zRWutXZvIaG9SpsYK6_TKL9LVVI8DGI"
worksheet = None

try:
    if not os.path.exists("service_account.json"):
        print("❌ service_account.json NOT FOUND!")
    else:
        SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        worksheet = sh.sheet1
        print("✅ SUCCESS: Connected to Google Sheet!")
except Exception as e:
    print(f"❌ Connection Error: {e}")

# Ensure Headers exist in the Sheet
if worksheet:
    try:
        headers = ["Timestamp", "Name", "Mobile", "Email", "City", "Qualification",
                   "Specialization", "Status", "Experience", "Interest", "LearningMode",
                   "Batch", "StartTime", "SAPModule", "LeadCategory"]
        if len(worksheet.get_all_values()) == 0:
            worksheet.append_row(headers)
            print("✅ Headers created")
    except Exception as e:
        print(f"⚠️ Header check failed: {e}")

# ==================== SELECTION DATA ====================
QUALIFICATIONS = ["12th Pass", "Diploma", "B.Com", "M.Com", "BBA", "MBA", "BCA", "MCA", "B.Tech / BE", "M.Tech", "Other"]
STATUS = ["Student", "Fresher", "Working Professional", "Business Owner", "Job Seeker"]
INTERESTS = ["Finance & Accounting", "Human Resources", "Sales", "Supply Chain", "Software Development", "Cloud & Infrastructure", "Analytics", "Project Management"]
MODES = ["Online", "Offline", "Hybrid"]
BATCHES = ["Weekday(Evening)", "Weekend"]
STARTS = ["Immediately", "Within 15 Days", "Within 1 Month", "Within 3 Months", "Just Exploring"]

def get_specs(qualification):
    mapping = {
        "B.Tech / BE": ["Computer Science", "IT", "Mechanical", "Electrical", "Electronics", "Civil", "Other"],
        "M.Tech": ["Computer Science", "IT", "Mechanical", "Electrical", "Electronics", "Civil", "Other"],
        "B.Com": ["Accounting", "Finance", "Taxation", "Auditing", "Banking"],
        "M.Com": ["Accounting", "Finance", "Taxation", "Auditing", "Banking"],
        "BBA": ["Finance", "HR", "Marketing", "Operations", "Supply Chain", "Business Analytics"],
        "MBA": ["Finance", "HR", "Marketing", "Operations", "Supply Chain", "Business Analytics"],
        "BCA": ["Software Development", "Cloud", "Database", "Analytics", "Networking"],
        "MCA": ["Software Development", "Cloud", "Database", "Analytics", "Networking"],
        "Diploma": ["Mechanical", "Civil", "Electrical", "Electronics", "Computer", "IT"],
        "12th Pass": ["Commerce", "Science", "Arts"],
    }
    return mapping.get(qualification, ["Other"])

def recommend_module(data):
    s = str(data.get("specialization", "")).lower()
    i = str(data.get("interest", "")).lower()
    rules = [
        (["accounting", "finance", "taxation", "auditing", "banking"], "SAP FICO"),
        (["hr"], "SAP SuccessFactors"),
        (["marketing"], "SAP SD"),
        (["supply chain", "operations"], "SAP MM"),
        (["software", "development"], "SAP ABAP"),
        (["cloud", "network", "database", "it"], "SAP BASIS"),
        (["analytics"], "SAP BW / SAC"),
        (["mechanical"], "SAP PM"),
        (["civil"], "SAP PS"),
    ]
    for keywords, module in rules:
        if any(k in s for k in keywords):
            return module
    if "finance" in i: return "SAP FICO"
    if any(x in i for x in ["human", "hr"]): return "SAP SuccessFactors"
    if "sales" in i: return "SAP SD"
    if "supply" in i: return "SAP MM"
    if "software" in i: return "SAP ABAP"
    if "cloud" in i: return "SAP BASIS"
    if "analytics" in i: return "SAP BW / SAC"
    return "SAP MM"

def lead_category(data):
    score = 0
    if data.get("status") == "Working Professional": score += 40
    if data.get("start") == "Immediately": score += 30
    if data.get("email"): score += 15
    if data.get("mobile"): score += 15
    if data.get("mode"): score += 10
    if score >= 80: return "HOT 🔥"
    if score >= 50: return "WARM 🟡"
    return "COLD ⚪"

def save_lead(data, module, category):
    if not worksheet:
        print("⚠️ Sheet not connected - Lead not saved")
        return
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("name", ""), data.get("mobile", ""), data.get("email", ""),
        data.get("city", ""), data.get("qualification", ""),
        data.get("specialization", ""), data.get("status", ""),
        data.get("experience", "NA"), data.get("interest", ""),
        data.get("mode", ""), data.get("batch", ""),
        data.get("start", ""), module, category
    ]
    try:
        worksheet.append_row(row)
        print(f"✅ Lead SAVED: {data.get('name')}")
    except Exception as e:
        print(f"❌ Save Failed: {e}")

# ==================== API ENDPOINTS ====================

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "service": "SAP Career Counseling API",
        "google_sheets_connected": worksheet is not None
    }), 200

@app.route('/process', methods=['POST'])
def process():
    req = request.get_json() or {}
    msg = req.get('message', '').strip()
    step = req.get('step', 0)
    data = req.get('data', {})

    bot_msg = ""
    show_options = False
    options = []

    if step == 0:
        data['name'] = msg
        bot_msg = "Please enter your <strong>Mobile Number</strong>:"
        step = 1
    elif step == 1:
        if not re.match(r'^\+?\d{10,15}$', msg):
            bot_msg = "❌ Please enter a valid mobile number."
        else:
            data['mobile'] = msg
            bot_msg = "Please enter your <strong>Email Address</strong>:"
            step = 2
    elif step == 2:
        if "@" not in msg or "." not in msg.split("@")[-1]:
            bot_msg = "❌ Please enter a valid email address."
        else:
            data['email'] = msg
            bot_msg = "Which <strong>City</strong> are you located in?"
            step = 3
    elif step == 3:
        data['city'] = msg
        bot_msg = "Select your <strong>Highest Qualification</strong>:"
        step = 4
        show_options = True
        options = QUALIFICATIONS
    elif step == 4:
        data['qualification'] = msg
        step = 5
        bot_msg = "Select your <strong>Specialization</strong>:"
        show_options = True
        options = get_specs(data['qualification'])
    elif step == 5:
        data['specialization'] = msg
        step = 6
        bot_msg = "Select your <strong>Current Status</strong>:"
        show_options = True
        options = STATUS
    elif step == 6:
        data['status'] = msg
        if msg == "Working Professional":
            step = 7
            bot_msg = "How many years of <strong>experience</strong> do you have?"
            show_options = True
            options = ["0-1 Years", "1-3 Years", "3-5 Years", "5-10 Years", "10+ Years"]
        else:
            data['experience'] = "NA"
            step = 8
            bot_msg = "Select your <strong>Interest Area</strong>:"
            show_options = True
            options = INTERESTS
    elif step == 7:
        data['experience'] = msg
        step = 8
        bot_msg = "Select your <strong>Interest Area</strong>:"
        show_options = True
        options = INTERESTS
    elif step == 8:
        data['interest'] = msg
        step = 9
        bot_msg = "Preferred <strong>Learning Mode</strong>?"
        show_options = True
        options = MODES
    elif step == 9:
        data['mode'] = msg
        step = 10
        bot_msg = "Preferred <strong>Batch</strong>?"
        show_options = True
        options = BATCHES
    elif step == 10:
        data['batch'] = msg
        step = 11
        bot_msg = "When would you like to <strong>start</strong> training?"
        show_options = True
        options = STARTS
    elif step == 11:
        data['start'] = msg
        module = recommend_module(data)
        category = lead_category(data)
        save_lead(data, module, category)
        duration = "1.5 months" if data.get("batch") == "Weekend" else "2.5 months"

        bot_msg = f"""🎯 <strong>SAP Career Assessment Complete!</strong><br><br>
<strong>Student Details:</strong><br>
• Name: <strong>{data.get('name')}</strong><br>
• Qualification: {data.get('qualification')}<br>
• Specialization: {data.get('specialization')}<br>
• Status: {data.get('status')}<br>
• Interest: {data.get('interest')}<br><br>
<strong>Recommended Program:</strong><br>
• Module: <strong>{module}</strong><br>
• Duration: {duration}<br>
• Batch: {data.get('batch')}<br>
• Mode: {data.get('mode')}<br><br>
Our counselor will contact you soon. Thank you! 🚀"""
        step = 999

    return jsonify({
        "bot_msg": bot_msg,
        "step": step,
        "data": data,
        "show_options": show_options,
        "options": options
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
