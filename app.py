from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import re
import requests
from html import escape

app = Flask(__name__)
CORS(app)

# ============================================================
# GOOGLE FORM CONFIGURATION
# ============================================================

GOOGLE_FORM_ID = "1FAIpQLSdm05Gr1FwFN6CHuxX3Lz5e81TQXexo0UySENOipD97bhUQsw"

GOOGLE_FORM_URL = (
    f"https://docs.google.com/forms/d/e/"
    f"{GOOGLE_FORM_ID}/formResponse"
)

# Google Form entry IDs
FORM_FIELDS = {
    "name": "entry.1908512028",
    "mobile": "entry.238731149",
    "email": "entry.111618526",
    "city": "entry.2128524278",
    "qualification": "entry.889944555",
    "specialization": "entry.98346018",
    "status": "entry.2010454129",
    "interest": "entry.80994627",
    "mode": "entry.1098585676",
    "batch": "entry.1721355342",
    "start": "entry.878633168",
    "module": "entry.174376127",
    "category": "entry.741317934",
}

# ============================================================
# SELECTION DATA
# ============================================================

QUALIFICATIONS = [
    "12th Pass",
    "Diploma",
    "B.Com",
    "M.Com",
    "BBA",
    "MBA",
    "BCA",
    "MCA",
    "B.Tech / BE",
    "M.Tech",
    "Other"
]

STATUS = [
    "Student",
    "Fresher",
    "Working Professional",
    "Business Owner",
    "Job Seeker"
]

INTERESTS = [
    "Finance & Accounting",
    "Human Resources",
    "Sales",
    "Supply Chain",
    "Software Development",
    "Cloud & Infrastructure",
    "Analytics",
    "Project Management"
]

MODES = [
    "Online",
    "Offline",
    "Hybrid"
]

BATCHES = [
    "Weekday(Evening)",
    "Weekend"
]

STARTS = [
    "Immediately",
    "Within 15 Days",
    "Within 1 Month",
    "Within 3 Months",
    "Just Exploring"
]


def get_specs(qualification):

    mapping = {

        "B.Tech / BE": [
            "Computer Science",
            "IT",
            "Mechanical",
            "Electrical",
            "Electronics",
            "Civil",
            "Other"
        ],

        "M.Tech": [
            "Computer Science",
            "IT",
            "Mechanical",
            "Electrical",
            "Electronics",
            "Civil",
            "Other"
        ],

        "B.Com": [
            "Accounting",
            "Finance",
            "Taxation",
            "Auditing",
            "Banking"
        ],

        "M.Com": [
            "Accounting",
            "Finance",
            "Taxation",
            "Auditing",
            "Banking"
        ],

        "BBA": [
            "Finance",
            "HR",
            "Marketing",
            "Operations",
            "Supply Chain",
            "Business Analytics"
        ],

        "MBA": [
            "Finance",
            "HR",
            "Marketing",
            "Operations",
            "Supply Chain",
            "Business Analytics"
        ],

        "BCA": [
            "Software Development",
            "Cloud",
            "Database",
            "Analytics",
            "Networking"
        ],

        "MCA": [
            "Software Development",
            "Cloud",
            "Database",
            "Analytics",
            "Networking"
        ],

        "Diploma": [
            "Mechanical",
            "Civil",
            "Electrical",
            "Electronics",
            "Computer",
            "IT"
        ],

        "12th Pass": [
            "Commerce",
            "Science",
            "Arts"
        ]
    }

    return mapping.get(qualification, ["Other"])


# ============================================================
# SAP MODULE RECOMMENDATION
# ============================================================

def recommend_module(data):

    specialization = str(
        data.get("specialization", "")
    ).lower()

    interest = str(
        data.get("interest", "")
    ).lower()

    rules = [

        (
            ["accounting", "finance", "taxation", "auditing", "banking"],
            "SAP FICO"
        ),

        (
            ["hr"],
            "SAP SuccessFactors"
        ),

        (
            ["marketing"],
            "SAP SD"
        ),

        (
            ["supply chain", "operations"],
            "SAP MM"
        ),

        (
            ["software", "development"],
            "SAP ABAP"
        ),

        (
            ["cloud", "network", "database", "it"],
            "SAP BASIS"
        ),

        (
            ["analytics"],
            "SAP BW / SAC"
        ),

        (
            ["mechanical"],
            "SAP PM"
        ),

        (
            ["civil"],
            "SAP PS"
        )
    ]

    for keywords, module in rules:

        if any(keyword in specialization for keyword in keywords):
            return module

    if "finance" in interest:
        return "SAP FICO"

    if any(x in interest for x in ["human", "hr"]):
        return "SAP SuccessFactors"

    if "sales" in interest:
        return "SAP SD"

    if "supply" in interest:
        return "SAP MM"

    if "software" in interest:
        return "SAP ABAP"

    if "cloud" in interest:
        return "SAP BASIS"

    if "analytics" in interest:
        return "SAP BW / SAC"

    return "SAP MM"


# ============================================================
# LEAD CATEGORY
# ============================================================

def lead_category(data):

    score = 0

    if data.get("status") == "Working Professional":
        score += 40

    if data.get("start") == "Immediately":
        score += 30

    if data.get("email"):
        score += 15

    if data.get("mobile"):
        score += 15

    if data.get("mode"):
        score += 10

    if score >= 80:
        return "HOT"

    if score >= 50:
        return "WARM"

    return "COLD"


# ============================================================
# GOOGLE FORM SUBMISSION
# ============================================================

def submit_to_google_form(data, module, category):

    payload = {

        FORM_FIELDS["name"]:
            data.get("name", ""),

        FORM_FIELDS["mobile"]:
            data.get("mobile", ""),

        FORM_FIELDS["email"]:
            data.get("email", ""),

        FORM_FIELDS["city"]:
            data.get("city", ""),

        FORM_FIELDS["qualification"]:
            data.get("qualification", ""),

        FORM_FIELDS["specialization"]:
            data.get("specialization", ""),

        FORM_FIELDS["status"]:
            data.get("status", ""),

        FORM_FIELDS["interest"]:
            data.get("interest", ""),

        FORM_FIELDS["mode"]:
            data.get("mode", ""),

        FORM_FIELDS["batch"]:
            data.get("batch", ""),

        FORM_FIELDS["start"]:
            data.get("start", ""),

        FORM_FIELDS["module"]:
            module,

        FORM_FIELDS["category"]:
            category
    }

    try:

        response = requests.post(
            GOOGLE_FORM_URL,
            data=payload,
            timeout=15,
            allow_redirects=True
        )

        print(
            "Google Form submission:",
            response.status_code
        )

        if response.status_code == 200:
            print("✅ GOOGLE FORM SUBMITTED")
            return True

        print(
            "⚠️ Google Form returned:",
            response.status_code
        )

        return False

    except Exception as e:

        print(
            "❌ Google Form submission failed:",
            str(e)
        )

        return False


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def health_check():

    return jsonify({

        "status": "online",

        "service":
            "SAP Career Counseling API",

        "google_form":
            "configured",

        "google_form_submission":
            "enabled"

    }), 200


# ============================================================
# CHATBOT PROCESS
# ============================================================

@app.route("/process", methods=["POST"])
def process():

    req = request.get_json() or {}

    msg = str(
        req.get("message", "")
    ).strip()

    step = req.get("step", 0)

    data = req.get("data", {})

    if not isinstance(data, dict):
        data = {}

    bot_msg = ""

    show_options = False

    options = []

    # --------------------------------------------------------
    # STEP 0 - NAME
    # --------------------------------------------------------

    if step == 0:

        if not msg:

            bot_msg = "❌ Please enter your name."

        else:

            data["name"] = msg

            bot_msg = (
                "Please enter your "
                "<strong>Mobile Number</strong>:"
            )

            step = 1

    # --------------------------------------------------------
    # STEP 1 - MOBILE
    # --------------------------------------------------------

    elif step == 1:

        if not re.match(
            r"^\+?\d{10,15}$",
            msg
        ):

            bot_msg = (
                "❌ Please enter a valid "
                "mobile number."
            )

        else:

            data["mobile"] = msg

            bot_msg = (
                "Please enter your "
                "<strong>Email Address</strong>:"
            )

            step = 2

    # --------------------------------------------------------
    # STEP 2 - EMAIL
    # --------------------------------------------------------

    elif step == 2:

        email_pattern = (
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        if not re.match(
            email_pattern,
            msg
        ):

            bot_msg = (
                "❌ Please enter a valid "
                "email address."
            )

        else:

            data["email"] = msg

            bot_msg = (
                "Which <strong>City</strong> "
                "are you located in?"
            )

            step = 3

    # --------------------------------------------------------
    # STEP 3 - CITY
    # --------------------------------------------------------

    elif step == 3:

        data["city"] = msg

        bot_msg = (
            "Select your "
            "<strong>Highest Qualification</strong>:"
        )

        step = 4

        show_options = True

        options = QUALIFICATIONS

    # --------------------------------------------------------
    # STEP 4 - QUALIFICATION
    # --------------------------------------------------------

    elif step == 4:

        data["qualification"] = msg

        bot_msg = (
            "Select your "
            "<strong>Specialization</strong>:"
        )

        step = 5

        show_options = True

        options = get_specs(
            data["qualification"]
        )

    # --------------------------------------------------------
    # STEP 5 - SPECIALIZATION
    # --------------------------------------------------------

    elif step == 5:

        data["specialization"] = msg

        bot_msg = (
            "Select your "
            "<strong>Current Status</strong>:"
        )

        step = 6

        show_options = True

        options = STATUS

    # --------------------------------------------------------
    # STEP 6 - STATUS
    # --------------------------------------------------------

    elif step == 6:

        data["status"] = msg

        if msg == "Working Professional":

            bot_msg = (
                "How many years of "
                "<strong>experience</strong> "
                "do you have?"
            )

            step = 7

            show_options = True

            options = [
                "0-1 Years",
                "1-3 Years",
                "3-5 Years",
                "5-10 Years",
                "10+ Years"
            ]

        else:

            data["experience"] = "NA"

            bot_msg = (
                "Select your "
                "<strong>Interest Area</strong>:"
            )

            step = 8

            show_options = True

            options = INTERESTS

    # --------------------------------------------------------
    # STEP 7 - EXPERIENCE
    # --------------------------------------------------------

    elif step == 7:

        data["experience"] = msg

        bot_msg = (
            "Select your "
            "<strong>Interest Area</strong>:"
        )

        step = 8

        show_options = True

        options = INTERESTS

    # --------------------------------------------------------
    # STEP 8 - INTEREST
    # --------------------------------------------------------

    elif step == 8:

        data["interest"] = msg

        bot_msg = (
            "Preferred "
            "<strong>Learning Mode</strong>?"
        )

        step = 9

        show_options = True

        options = MODES

    # --------------------------------------------------------
    # STEP 9 - MODE
    # --------------------------------------------------------

    elif step == 9:

        data["mode"] = msg

        bot_msg = (
            "Preferred "
            "<strong>Batch</strong>?"
        )

        step = 10

        show_options = True

        options = BATCHES

    # --------------------------------------------------------
    # STEP 10 - BATCH
    # --------------------------------------------------------

    elif step == 10:

        data["batch"] = msg

        bot_msg = (
            "When would you like to "
            "<strong>start</strong> training?"
        )

        step = 11

        show_options = True

        options = STARTS

    # --------------------------------------------------------
    # STEP 11 - FINAL SUBMISSION
    # --------------------------------------------------------

    elif step == 11:

        data["start"] = msg

        # Calculate recommendation
        module = recommend_module(data)

        # Calculate lead category
        category = lead_category(data)

        # Submit to Google Form
        submitted = submit_to_google_form(
            data,
            module,
            category
        )

        # Duration
        if data.get("batch") == "Weekend":
            duration = "1.5 months"
        else:
            duration = "2.5 months"

        safe_name = escape(
            str(data.get("name", ""))
        )

        safe_qualification = escape(
            str(data.get("qualification", ""))
        )

        safe_specialization = escape(
            str(data.get("specialization", ""))
        )

        safe_status = escape(
            str(data.get("status", ""))
        )

        safe_interest = escape(
            str(data.get("interest", ""))
        )

        safe_module = escape(
            str(module)
        )

        safe_batch = escape(
            str(data.get("batch", ""))
        )

        safe_mode = escape(
            str(data.get("mode", ""))
        )

        bot_msg = f"""
🎯 <strong>SAP Career Assessment Complete!</strong>
<br><br>

<strong>Student Details:</strong>
<br>
• Name: <strong>{safe_name}</strong>
<br>
• Qualification: {safe_qualification}
<br>
• Specialization: {safe_specialization}
<br>
• Status: {safe_status}
<br>
• Interest: {safe_interest}
<br><br>

<strong>Recommended Program:</strong>
<br>
• Module: <strong>{safe_module}</strong>
<br>
• Duration: {duration}
<br>
• Batch: {safe_batch}
<br>
• Mode: {safe_mode}
<br><br>
"""

        if submitted:

            bot_msg += """
✅ <strong>Your details have been successfully submitted.</strong>
<br><br>
Our counselor will contact you soon. Thank you! 🚀
"""

        else:

            bot_msg += """
⚠️ Your assessment is complete, but we could not submit your details right now.
<br><br>
Please try again or contact our counselor.
"""

        step = 999

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({

        "bot_msg": bot_msg,

        "step": step,

        "data": data,

        "show_options": show_options,

        "options": options

    }), 200


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
