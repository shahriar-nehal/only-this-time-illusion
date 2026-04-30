import subprocess
import time
import csv
import re
from datetime import datetime

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
INPUT_FILE = "target_apks.csv"
EVENT_LOG_FILE = "results_events.csv"
SUMMARY_FILE = "results_summary.csv"

POLL_INTERVAL_SEC = 2
ACTIVE_WINDOW_MS = 5000 

# --------------------------------------------------------------------
# ADB helper
# --------------------------------------------------------------------
def run_cmd(command):
    try:
        result = subprocess.run(
            f"adb shell {command}",
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout.strip()
    except Exception:
        return ""

def load_targets():
    target_map = {}
    category_map = {}
    with open(INPUT_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pkg = row['Package Name'].strip()
            app = row['App Name'].strip()
            cat = row.get('Category', '').strip()
            target_map[pkg] = app
            category_map[pkg] = cat
    return target_map, category_map

# --------------------------------------------------------------------
# Core Parser
# --------------------------------------------------------------------
def parse_duration_to_ms(duration_str):
    s = duration_str.replace('-', '').replace('+', '')
    total_ms = 0
    ms_match = re.search(r'(\d+)ms', s)
    if ms_match:
        total_ms += int(ms_match.group(1))
        s = re.sub(r'\d+ms', '', s)
    s_match = re.search(r'(\d+)s', s)
    if s_match: total_ms += int(s_match.group(1)) * 1000
    m_match = re.search(r'(\d+)m', s)
    if m_match: total_ms += int(m_match.group(1)) * 60 * 1000
    h_match = re.search(r'(\d+)h', s)
    if h_match: total_ms += int(h_match.group(1)) * 60 * 60 * 1000
    d_match = re.search(r'(\d+)d', s)
    if d_match: total_ms += int(d_match.group(1)) * 24 * 60 * 60 * 1000
    return total_ms

def parse_appops_for_location():
    out = run_cmd("dumpsys appops --op FINE_LOCATION")
    if not out: return {}

    active_apps = {}
    current_pkg = None

    for line in out.splitlines():
        line = line.rstrip()
        if line.strip().startswith("Package "):
            m = re.match(r"\s*Package\s+([^\s:]+):", line)
            if m:
                current_pkg = m.group(1)
                active_apps[current_pkg] = {"state": "UNKNOWN", "age_ms": float('inf')}
            continue
        if line.strip().startswith("Uid "):
            current_pkg = None
            continue
        if current_pkg is None: continue

        if "Access:" in line or "Reject:" in line:
            m = re.search(r"(?:Access|Reject):\s*\[([^\]]+)\][^(]*\(([-+][^)]+)\)", line)
            if not m: continue

            state_token = m.group(1)
            duration_str = m.group(2)
            state_name = state_token.split('-')[0]
            age_ms = parse_duration_to_ms(duration_str)

            new_state = None
            if state_name == "top": new_state = "top"
            elif state_name == "fg": new_state = "fg"
            elif state_name == "fgsvc": new_state = "fgsvc"
            elif state_name == "bg": new_state = "bg"

            if new_state:
                if age_ms < active_apps[current_pkg]["age_ms"]:
                    active_apps[current_pkg] = {"state": new_state, "age_ms": age_ms}

    final_active_apps = {}
    for pkg, data in active_apps.items():
        if data["state"] == "UNKNOWN": continue
        if data["age_ms"] <= ACTIVE_WINDOW_MS:
            final_active_apps[pkg] = data["state"]

    return final_active_apps

# --------------------------------------------------------------------
# Checks & Logic
# --------------------------------------------------------------------
def is_service_running(pkg):
    out = run_cmd(f"dumpsys activity services {pkg}")
    return "ServiceRecord" in out

def check_notification_exists(pkg):
    out = run_cmd("dumpsys notification --noredact")
    if not out: return False
    for line in out.splitlines():
        if "NotificationRecord{" in line and f"pkg={pkg}" in line:
            return True
    return False

def analyze_verdict(state, has_notification, duration_sec):
    if state == "bg":
        return "SAFE (Normal Background)"
    if state in ("top", "fg"):
        return "SAFE (Legitimate Foreground)"
    if state == "fgsvc":
        if has_notification:
            return "SAFE (Legitimate Foreground with Notification)"
        else:
            if duration_sec < 5:
                return f"WARNING (Invisible Service - Active for {duration_sec}s)"
            else:
                return f"CRITICAL (Invisible Service - PERSISTENT for {duration_sec}s)"
    return "UNKNOWN"

def choose_more_severe_verdict(prev, new):
    def severity(v):
        if v.startswith("CRITICAL"): return 4
        if v.startswith("WARNING"): return 3
        if v.startswith("SAFE (Legitimate Foreground with"): return 2
        if v.startswith("SAFE (Legitimate"): return 1
        return 0
    return new if severity(new) > severity(prev) else prev

# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------
def main():
    target_map, category_map = load_targets()
    fgsvc_start_times = {} 
    last_logged_state = {}
    final_verdicts = {pkg: "Not Tested" for pkg in target_map}

    event_log_f = open(EVENT_LOG_FILE, 'w', newline='', encoding='utf-8')
    event_writer = csv.writer(event_log_f)
    event_writer.writerow(["Timestamp", "App Name", "Package Name", "State", "Duration", "Verdict"])

    print(f"[*] Loaded {len(target_map)} targets.")
    print(f"[*] Strict Mode Active: Ignoring logs older than {ACTIVE_WINDOW_MS/1000}s.")
    print("[*] Start your 'Kill Test' now.")
    print("-" * 115)
    print(f"{'TIME':<8} | {'APP NAME':<20} | {'STATE':<8} | {'VERDICT'}")
    print("-" * 115)

    try:
        while True:
            current_active = parse_appops_for_location()
            active_targets_this_cycle = set()

            for pkg, state in current_active.items():
                if pkg not in target_map: continue
                
                # Proof of life
                if state == "fgsvc":
                    if not is_service_running(pkg):
                        continue
                
                active_targets_this_cycle.add(pkg)
                app_name = target_map[pkg]

                duration_sec = 0
                if state == "fgsvc":
                    if pkg not in fgsvc_start_times:
                        fgsvc_start_times[pkg] = time.time()
                    duration_sec = int(time.time() - fgsvc_start_times[pkg])
                else:
                    if pkg in fgsvc_start_times:
                        del fgsvc_start_times[pkg]

                has_notification = False
                if state == "fgsvc":
                    has_notification = check_notification_exists(pkg)

                verdict = analyze_verdict(state, has_notification, duration_sec)
                
                # Update Final Verdict Summary
                prev_verdict = final_verdicts.get(pkg, "Not Tested")
                final_verdicts[pkg] = choose_more_severe_verdict(prev_verdict, verdict)

                should_log = (state != last_logged_state.get(pkg)) or (state == "fgsvc")

                if should_log:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"{timestamp:<8} | {app_name[:20]:<20} | {state:<8} | {verdict}")

                    event_writer.writerow([
                        datetime.now().isoformat(timespec='seconds'),
                        app_name, pkg, state, f"{duration_sec}s", verdict
                    ])
                    event_log_f.flush()
                    last_logged_state[pkg] = state

            stale_pkgs = [p for p in last_logged_state if p not in active_targets_this_cycle]
            for p in stale_pkgs:
                del last_logged_state[p]
                if p in fgsvc_start_times: del fgsvc_start_times[p]

            time.sleep(POLL_INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\n[*] Stopping scan.")
    finally:
        event_log_f.close()
        print(f"[*] Writing summary to {SUMMARY_FILE}...")
        with open(SUMMARY_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["App Name", "Package Name", "Category", "Final Verdict"])
            for pkg, verdict in final_verdicts.items():
                writer.writerow([
                    target_map[pkg],
                    pkg,
                    category_map.get(pkg, ""),
                    verdict
                ])
        print("[+] Done.")

if __name__ == "__main__":
    main()