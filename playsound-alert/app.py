from flask import Flask, render_template, send_from_directory, jsonify, send_file, request, session, redirect, url_for
import requests
#import json
from generate_report import load_json_from_file, filter_alerts_by_range, generate_csv, fetch_alert_groups, parse_args
import os
#from requests.auth import HTTPBasicAuth
import base64


app = Flask(__name__)
app.secret_key = 'abcd'  # Replace with a strong secret

ALLOWED_USERS_nano_bsc = {
    "admin",
    "noc-ro",
    "noc-1",
    "nanobsc"
}
ALLOWED_USERS_smsc = {
    "noc-ro",
    "noc-1",
    "nanobsc"
}
GRAFANA_URL = "https://grafana.yahsat.ae"
@app.route("/login-ui", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    source   = data.get("source")
    print("Before login session:", dict(session))

    if source == "/ipa":
        ALLOWED_USERS = ALLOWED_USERS_nano_bsc
    elif source == "/tango":
        ALLOWED_USERS = ALLOWED_USERS_smsc
    else:
        ALLOWED_USERS = set()

    if username not in ALLOWED_USERS:
        return jsonify({"success": False, "message": "Access denied"}), 403

    # Encode the credentials manually like: base64("username:password")
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/org",
            headers=headers,
            verify=False  # Set to False if using self-signed certs
        )
    except requests.exceptions.RequestException as e:
        print("Error connecting to Grafana:", e)
        return jsonify({"success": False, "message": "Grafana unreachable"}), 503


    if response.status_code == 200:
        session["user"] = username
        session["logged_in"] = True
        print("After login session:", dict(session))
        return jsonify({"success": True})
    else:
        return jsonify({"success": False}), 401

@app.route("/logout-ui", methods=["GET", "POST"])
def logout_ui():
    try:
        next_page = request.args.get("next")
        print("Before login session:", dict(session))
        session.clear()
        print("After login session:", dict(session))
        return redirect(next_page)
    except Exception as e:
        print("Logout error:", e)
        return "Logout failed", 500

API_URL = "http://192.168.63.8:1880/api/v1/alert_groups/"
AUTH_TOKEN = "d38faf14c8585b897476d4316316e840a7f01c053724dcff297dedcfa6b44ee3"
HEADERS = {
    "Authorization": AUTH_TOKEN,
    "Content-Type": "application/json"
}
def fetch_all_alerts():
    page = 1
    all_alerts = []

    while True:
        response = requests.get(f"{API_URL}?page={page}&page_size=50", headers=HEADERS, verify=False)
        data = response.json()

        results = data.get("results", [])
        if not results:
            break

        all_alerts.extend(results)
        current_page = data.get("current_page_number")
        #print(f"current page {current_page} and ")
        if data.get("current_page_number") >= data.get("total_pages"):
            break
        page += 1

    return all_alerts

#DATA_FILE = "/home/shubhada/playsound-alerts/report.json"
def get_alert_status(grafana_folder):
    count = 0
    try:
     #   response = requests.get(
      #      API_URL,
       #     headers={
        #        "Authorization": AUTH_TOKEN,
         #       "Content-Type": "application/json"
          #  },
           # verify=False
        #)
        #data = response.json()
        #with open(DATA_FILE, "r") as f:
        #    data = json.load(f)
        alert_groups = fetch_all_alerts()
        for group in alert_groups:
            alerts = group.get("last_alert", {}).get("payload", {}).get("alerts", [])
            for alert in alerts:
                if alert.get("labels", {}).get("grafana_folder") == grafana_folder and group.get("state") == "firing":
                    count += 1


    except Exception as e:
        print("Error fetching alerts:", e)
    firing = count > 0
    return firing, count

@app.route("/ipa")
def index():
    return render_template("test.html")

@app.route("/tango")
def tango():
    return render_template("tango.html")

@app.route("/api/check/<grafana_folder>-Alarm")
def api_check(grafana_folder):
    firing, count = get_alert_status(grafana_folder)
    return jsonify({"firing": firing, "count": count})

@app.route("/download/nanobsc")
def download_nanobsc():
    date_range = request.args.get("date_range", "")
    file_format = request.args.get("format", "csv").lower()  # default to CSV
    try:
        from_date_str, to_date_str = [d.strip() for d in date_range.split("to")]
    except ValueError:
        return "Invalid date range format. Please use the date picker.", 400
    alert_groups = fetch_alert_groups(from_date_str, to_date_str)
    filtered = filter_alerts_by_range(alert_groups, from_date_str, to_date_str)
    generate_csv(filtered)  # This generates both files

    # Choose file to serve based on user format selection
    if file_format == "excel":
        file_path = "NanoBSC_Alarm_Report.xlsx"
    else:
        file_path = "NanoBSC_Alarm_Report.csv"

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        # Optional: customize this message
        return f"No NanoBSC alerts found for {from_date_str} to {to_date_str}. CSV not generated.", 404



@app.route("/download/smsc")
def download_smsc():
    date_range = request.args.get("date_range", "")
    file_format = request.args.get("format", "csv").lower()  # default to CSV
    try:
        from_date_str, to_date_str = [d.strip() for d in date_range.split("to")]
    except ValueError:
        return "Invalid date range format. Please use the date picker.", 400
    alert_groups = fetch_alert_groups(from_date_str, to_date_str)
    filtered = filter_alerts_by_range(alert_groups, from_date_str, to_date_str)
    generate_csv(filtered)
    # Choose file to serve based on user format selection
    if file_format == "excel":
        file_path = "SMSC_Alarm_Report.xlsx"
    else:
        file_path = "SMSC_Alarm_Report.csv"


    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        # Optional: customize this message
        return f"No SMSC alerts found for {from_date_str} to {to_date_str}. CSV not generated.", 404

@app.route("/api/oncall-alerts/nano-bsc")
def get_oncall_alerts():
    try:
       # res = requests.get(
       #     "http://192.168.63.8:1880/api/v1/alert_groups",
       #     headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
       # )
       # res = requests.get(f"{API_URL}", headers=HEADERS, verify=False)
       # data = res.

        alert_groups = fetch_all_alerts()


        # Optionally filter by folder name
        filtered = []
        for group in alert_groups:

            alerts = group.get("last_alert", {}).get("payload", {}).get("alerts", [])
            for alert in alerts:
                labels = alert.get("labels", {})
                if labels.get("grafana_folder") == "NanoBSC":

                    filtered.append(group)
                    break



        return jsonify({
        "results": filtered,
        "total": len(filtered)
        })


    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/oncall-alerts/smsc")
def get_oncall_alerts_smsc():
    try:
       # res = requests.get(
       #     "http://192.168.63.8:1880/api/v1/alert_groups",
       #     headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
       # )
       # res = requests.get(f"{API_URL}", headers=HEADERS, verify=False)
       # data = res.json()


        alert_groups = fetch_all_alerts()

        # Optionally filter by folder name
        filtered = []

        for group in alert_groups:
            state = group.get("state", "").lower()

            alerts = group.get("last_alert", {}).get("payload", {}).get("alerts", [])

            for alert in alerts:
                labels = alert.get("labels", {})

                if labels.get("grafana_folder") == "SMSC":

                    filtered.append(group)
                    break


        return jsonify({
        "results": filtered,
        "total": len(filtered),


    })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/oncall-alerts/<alert_id>/<action>", methods=["POST"])
def perform_oncall_action(alert_id, action):
    if action not in ["acknowledge", "resolve", "unacknowledge", "unresolve", "silence","unsilence"]:
        return jsonify({"error": "Invalid action"}), 400

    try:
       # res = requests.post(
       #     f"http://192.168.63.8:1880/api/v1/alert_groups/{alert_id}/{action}",
       #     headers={"Authorization": f"{AUTH_TOKEN}"}
       # )
       if action == "silence":
            payload = request.json or {}
            print(f"payload : {payload}")
            res = requests.post(f"{API_URL}{alert_id}/{action}", headers=HEADERS, json=payload, verify=False)
       else:
            res = requests.post(f"{API_URL}{alert_id}/{action}", headers=HEADERS, verify=False)

       if res.status_code == 200:
            API_URL_resol = "http://192.168.63.8:1880/api/v1/resolution_notes/"
            user = session.get("user")
            note_text = f"{action} by {user}"

            resolution_payload = {
            "alert_group_id": alert_id,
            "text":           note_text
            }
            res_resol = requests.post(f"{API_URL_resol}", headers=HEADERS, json=resolution_payload, verify=False)
            return jsonify({"status": "success"})
       else:
            return jsonify({
                "status": "error",
                "code": res.status_code,
                "message": res.get("message") if isinstance(res, dict) else str(res)
            }), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/oncall-alerts/timeline/<group_id>")
def oncall_timeline(group_id):
    username = session.get("user")

    #if username not in ALLOWED_USERS:
    #    return jsonify({"error": "🚫 You are not authorized to view this timeline."}), 401

    GRAFANA_API = "https://grafana.yahsat.ae"
    auth_header = {
        "Authorization": "Basic bm9jLXJvOm5vY3JvQDEyMw=="  # <-- Replace with secure method!
    }

    try:
        res = requests.get(
            f"{GRAFANA_API}/api/plugins/grafana-oncall-app/resources/alertgroups/{group_id}/",
            headers=auth_header,
            verify=False  # only if self-signed cert
        )
        res.raise_for_status()
        full_data = res.json()
        return jsonify(full_data.get("render_after_resolve_report_json", []))
    except Exception as e:
        print("Timeline API failed:", e)
        return jsonify([]), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8190)
