# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import firebase_admin
# from firebase_admin import credentials, firestore
# import datetime
# import os

# app = Flask(__name__)
# CORS(app)

# # ---- Firebase init ----
# # Expect a service account JSON file at backend/serviceAccountKey.json
# # or set FIREBASE_CREDS_JSON env var to the JSON string.
# def init_firestore():
#     if firebase_admin._apps:
#         return firestore.client()

#     creds_path = os.getenv("FIREBASE_CREDS_PATH", "serviceAccountKey.json")
#     creds_json = os.getenv("FIREBASE_CREDS_JSON")

#     if creds_json:
#         cred = credentials.Certificate(json.loads(creds_json))
#     else:
#         if not os.path.exists(creds_path):
#             raise FileNotFoundError(
#                 "serviceAccountKey.json not found. Place it in backend/ or set FIREBASE_CREDS_JSON"
#             )
#         cred = credentials.Certificate(creds_path)

#     firebase_admin.initialize_app(cred)
#     return firestore.client()

# db = None
# try:
#     import json  # noqa
#     db = init_firestore()
# except Exception as e:
#     print("WARNING: Firestore not initialized yet:", e)
#     db = None

# # ---- Helpers ----
# REQUIRED_FIELDS = ["location", "sector", "description"]

# def validate_report(data):
#     for f in REQUIRED_FIELDS:
#         if f not in data:
#             return False, f"Missing field: {f}"
#     loc = data.get("location", {})
#     if not isinstance(loc, dict) or "lat" not in loc or "lng" not in loc:
#         return False, "location must be an object with lat and lng"
#     return True, ""

# # ---- Routes ----
# @app.route("/api/health", methods=["GET"])
# def health():
#     return jsonify({"status": "ok", "firestore": db is not None})

# @app.route("/api/submit", methods=["POST"])
# def submit_report():
#     if db is None:
#         return jsonify({"error": "Firestore not initialized"}), 500
#     data = request.get_json(force=True, silent=True) or {}
#     ok, msg = validate_report(data)
#     if not ok:
#         return jsonify({"error": msg}), 400

#     now = datetime.datetime.utcnow().isoformat()
#     data["timestamp"] = now
#     # Normalize
#     data["sector"] = str(data.get("sector", "")).strip()[:64]
#     try:
#         amount = data.get("amount")
#         data["amount"] = float(amount) if amount not in (None, "") else None
#     except Exception:
#         data["amount"] = None

#     # Optional fields
#     data["channel"] = data.get("channel", "web")
#     data["city"] = data.get("city", None)

#     doc_ref = db.collection("reports").add(data)
#     return jsonify({"message": "Report submitted", "id": doc_ref[1].id})

# @app.route("/api/reports", methods=["GET"])
# def get_reports():
#     if db is None:
#         return jsonify({"error": "Firestore not initialized"}), 500
#     # Optional filters
#     sector = request.args.get("sector")
#     since = request.args.get("since")  # ISO date
#     q = db.collection("reports")
#     if sector:
#         q = q.where("sector", "==", sector)
#     if since:
#         try:
#             # naive string compare works for ISO timestamps, but we can parse to datetime if needed
#             pass
#         except Exception:
#             pass
#     docs = q.stream()
#     reports = []
#     for d in docs:
#         obj = d.to_dict()
#         obj["id"] = d.id
#         reports.append(obj)
#     return jsonify(reports)

# @app.route("/api/stats", methods=["GET"])
# def get_stats():
#     if db is None:
#         return jsonify({"error": "Firestore not initialized"}), 500
#     # Very simple in-API aggregation (client can also aggregate)
#     docs = db.collection("reports").stream()
#     sector_counts = {}
#     city_counts = {}
#     total_reports = 0
#     total_amount = 0.0
#     amount_count = 0

#     for d in docs:
#         r = d.to_dict()
#         total_reports += 1
#         sec = r.get("sector") or "Unknown"
#         sector_counts[sec] = sector_counts.get(sec, 0) + 1
#         city = r.get("city") or "Unknown"
#         city_counts[city] = city_counts.get(city, 0) + 1
#         amt = r.get("amount")
#         if isinstance(amt, (int, float)):
#             total_amount += float(amt)
#             amount_count += 1

#     avg_amount = (total_amount / amount_count) if amount_count else 0.0
#     return jsonify({
#         "total_reports": total_reports,
#         "sector_counts": sector_counts,
#         "city_counts": city_counts,
#         "avg_amount": round(avg_amount, 2)
#     })

# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 5000))
#     app.run(host="0.0.0.0", port=port, debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import datetime
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# ---- MongoDB init ----
def init_mongo():
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB", "mydatabase")
    if not mongo_uri:
        raise ValueError("MONGO_URI not set in environment variables")
    client = MongoClient(mongo_uri)
    return client[db_name]

db = None
try:
    db = init_mongo()
    reports_col = db["reports"]
except Exception as e:
    print("WARNING: MongoDB not initialized:", e)
    db = None

# ---- Helpers ----
REQUIRED_FIELDS = ["location", "sector", "description"]

def validate_report(data):
    for f in REQUIRED_FIELDS:
        if f not in data:
            return False, f"Missing field: {f}"
    loc = data.get("location", {})
    if not isinstance(loc, dict) or "lat" not in loc or "lng" not in loc:
        return False, "location must be an object with lat and lng"
    return True, ""

# ---- Routes ----
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mongodb": db is not None})

@app.route("/api/submit", methods=["POST"])
def submit_report():
    if db is None:
        return jsonify({"error": "MongoDB not initialized"}), 500
    data = request.get_json(force=True, silent=True) or {}
    ok, msg = validate_report(data)
    if not ok:
        return jsonify({"error": msg}), 400

    now = datetime.datetime.utcnow().isoformat()
    data["timestamp"] = now
    data["sector"] = str(data.get("sector", "")).strip()[:64]

    try:
        amount = data.get("amount")
        data["amount"] = float(amount) if amount not in (None, "") else None
    except Exception:
        data["amount"] = None

    data["channel"] = data.get("channel", "web")
    data["city"] = data.get("city", None)

    result = reports_col.insert_one(data)
    return jsonify({"message": "Report submitted", "id": str(result.inserted_id)})

@app.route("/api/reports", methods=["GET"])
def get_reports():
    if db is None:
        return jsonify({"error": "MongoDB not initialized"}), 500
    sector = request.args.get("sector")
    query = {}
    if sector:
        query["sector"] = sector

    docs = reports_col.find(query)
    reports = []
    for d in docs:
        d["_id"] = str(d["_id"])  # Convert ObjectId to string
        reports.append(d)
    return jsonify(reports)

@app.route("/api/stats", methods=["GET"])
def get_stats():
    if db is None:
        return jsonify({"error": "MongoDB not initialized"}), 500

    docs = reports_col.find()
    sector_counts = {}
    city_counts = {}
    total_reports = 0
    total_amount = 0.0
    amount_count = 0

    for r in docs:
        total_reports += 1
        sec = r.get("sector") or "Unknown"
        sector_counts[sec] = sector_counts.get(sec, 0) + 1
        city = r.get("city") or "Unknown"
        city_counts[city] = city_counts.get(city, 0) + 1
        amt = r.get("amount")
        if isinstance(amt, (int, float)):
            total_amount += float(amt)
            amount_count += 1

    avg_amount = (total_amount / amount_count) if amount_count else 0.0
    return jsonify({
        "total_reports": total_reports,
        "sector_counts": sector_counts,
        "city_counts": city_counts,
        "avg_amount": round(avg_amount, 2)
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
