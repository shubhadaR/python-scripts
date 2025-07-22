import requests
from datetime import datetime, timedelta
import argparse
import csv


# ----------------------------
# Configuration
# ----------------------------
API_URL = "http://192.168.63.8:1880/api/v1/alert_groups/"
API_KEY = "d38faf14c8585b897476d4316316e840a7f01c053724dcff297dedcfa6b44ee3"

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

# ----------------------------
# Argument Parsing
# ----------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Generate Grafana OnCall Alert Report")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", required=True, help="End date (YYYY-MM-DD)")
    return parser.parse_args()


def load_json_from_file(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)
    return data


# ----------------------------
# Fetch Alert Group Data
# ----------------------------
def fetch_alert_groups(from_date_str, to_date_str):
    page = 1
    page_size = 50
    all_alerts = []

    # Convert to full ISO 8601 UTC format
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d").strftime("%Y-%m-%dT23:59:59Z")

    while True:
        url = (
            f"{API_URL}?page_size={page_size}"
            f"&page={page}"
        )
        response = requests.get(url, headers=HEADERS, verify=False)

        if response.status_code != 200:
            raise Exception(f"API failed (page {page}): {response.status_code}: {response.text}")

        data = response.json()
        alerts = data.get("results", [])
        total_pages = data.get("total_pages", page)

        if not alerts:
            print(f"[i] No alerts on page {page}.")
            break

        all_alerts.extend(alerts)
        print(f"[i] Page {page}/{total_pages}: {len(alerts)} alerts")

        if page >= total_pages:
            break

        page += 1

    return all_alerts


# ----------------------------
# Filter Alerts by Date Range
# ----------------------------
from datetime import timezone

def filter_alerts_by_range(alert_groups, from_date_str, to_date_str):
    # Make both aware by attaching UTC timezone
    from_dt = datetime.strptime(from_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    to_dt = datetime.strptime(to_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)

    filtered = []

    for group in alert_groups:
        created_at_str = group.get("created_at")
        if not created_at_str:
            continue
        try:
            # Convert to offset-aware UTC datetime
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if from_dt <= created_at < to_dt:
                filtered.append(group)
        except ValueError:
            continue

    print(f"[i] Filtered {len(filtered)} alerts between {from_dt.date()} and {(to_dt - timedelta(days=1)).date()}")
    return filtered




# ----------------------------
# Generate CSV Report
# ----------------------------
def generate_csv(alert_groups, filename='grafana_oncall_report.csv'):
    #report_data = []
    nanobsc_data = []
    smsc_data = []

    for group in alert_groups:
        last_alert = group.get('last_alert', {})
        payload = last_alert.get('payload', {})
        first_alert = payload.get('alerts', [{}])[0]
        labels = first_alert.get('labels', {})
        annotations = first_alert.get('annotations', {})

        #if not isinstance(group, dict):
        # continue
#
        #last_alert = group.get('last_alert') or {}
        #if not isinstance(last_alert, dict):
        #    continue
        ##payload = last_alert.get('payload', {})
        #alerts = payload.get('alerts', [])
        #first_alert = alerts[0] if alerts and isinstance(alerts[0], dict) else {}
#
        #labels = first_alert.get('labels', {}) if isinstance(first_alert, dict) else {}
        #annotations = first_alert.get('annotations', {}) if isinstance(first_alert, dict) else {}
#
        #alertname = labels.get('alertname', '')

        report_data=({
            'Alert ID': group.get('id'),
            'Created At': group.get('created_at'),
            'State': group.get('state'),
            'Title': group.get('title', '').strip(),
            'Hostname': labels.get('hostname', ''),
            'Service Name': labels.get('service_name', ''),
            'Alert Name': labels.get('alertname', ''),
            'Description': annotations.get('description', '')
        })
        grafana_folder = labels.get('grafana_folder')
        if grafana_folder == "NanoBSC":
            nanobsc_data.append(report_data)
        elif grafana_folder == "SMSC":
            smsc_data.append(report_data)
    #df = pd.DataFrame(report_data)
    #df.to_csv(filename, index=False)
    #print(f"[✔] CSV report saved to {filename}")

    def write_csv(filename, data):
        if not data:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"[🗑] Removed stale CSV: {filename}")
            print(f"[!] No data to write in {filename}")
            return
        fieldnames = data[0].keys()
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"[✔] Saved: {filename}")

    write_csv("NanoBSC_Alarm_Report.csv", nanobsc_data)
    write_csv("SMSC_Alarm_Report.csv", smsc_data)

    def write_excel(filename, data):
        if not data:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"[🗑] Removed stale Excel: {filename}")
            print(f"[!] No data to write in {filename}")
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "Alerts"

        # Write headers
        headers = list(data[0].keys())
        ws.append(headers)

        # Write rows
        for row in data:
            ws.append([row.get(header, '') for header in headers])

        wb.save(filename)
        print(f"[✔] Excel saved: {filename}")
    write_excel("NanoBSC_Alarm_Report.xlsx", nanobsc_data)
    write_excel("SMSC_Alarm_Report.xlsx", smsc_data)

# ----------------------------
# Generate PDF Report
# ----------------------------
#def generate_pdf(alert_groups, filename='grafana_oncall_report.pdf'):
#    pdf = FPDF()
#    pdf.add_page()
#    pdf.set_font("Arial", 'B', 14)
#    pdf.cell(200, 10, txt="Grafana OnCall Alert Report", ln=True, align='C')
#    pdf.set_font("Arial", size=10)
#
#    for group in alert_groups:
#        pdf.ln(5)
#        pdf.cell(200, 10, txt=f"Alert ID: {group.get('id')}", ln=True)
#        pdf.cell(200, 10, txt=f"Title: {group.get('title')}", ln=True)
#        pdf.cell(200, 10, txt=f"Status: {group.get('status')}", ln=True)
#        pdf.cell(200, 10, txt=f"Created At: {group.get('created_at')}", ln=True)
#        pdf.cell(200, 10, txt=f"Service: {group.get('service', {}).get('name', '')}", ln=True)
#        pdf.cell(200, 10, txt=f"Labels: {group.get('labels')}", ln=True)
#        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
#
#    pdf.output(filename)
#    print(f"[✔] PDF report saved to {filename}")
#
# ----------------------------
# Main Execution
# ----------------------------
def main():
    args = parse_args()

    try:
        print(f"[...] Fetching alert groups from Grafana OnCall API (last 3 days)")
        #data = fetch_alert_groups()
        #data = load_json_from_file("report.json")
        alert_groups = fetch_alert_groups(args.from_date, args.to_date)

        if not alert_groups:
            print("[!] No alert groups found.")
            return

        filtered_alerts = filter_alerts_by_range(alert_groups, args.from_date, args.to_date)

        if not filtered_alerts:
            print(f"[!] No alerts found from {args.from_date} to {args.to_date}.")
            return

        generate_csv(filtered_alerts)
        generate_pdf(filtered_alerts)

    except Exception as e:
        print(f"[✖] Error: {e}")

if __name__ == "__main__":
    main()

