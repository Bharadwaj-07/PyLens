import subprocess
import threading
import time
import json
import os
import shutil
import re
import argparse
from typing import List, Dict, Set

# Paths
HOME = os.path.expanduser("~")
FT_LOG = os.path.join(HOME, "function_tracker_stats.txt")
LM_LOG = os.path.join(HOME, "live_monitor_java.log")
FT_CLONE = os.path.join(HOME, "function_tracker_clone.txt")
LM_CLONE = os.path.join(HOME, "live_monitor_clone.txt")

FT_JSON = os.path.join(os.getcwd(), "function_tracker.json")
LM_JSON = os.path.join(os.getcwd(), "realtime_monitor.json")
FT_SUMMARY_JSON = os.path.join(os.getcwd(), "function_statistics.json")

# Storage
function_tracker_data = []

def ensure_files_exist():
    """Create empty files if they don't exist"""
    for path in [FT_LOG, LM_LOG, FT_CLONE, LM_CLONE]:
        if not os.path.exists(path):
            open(path, 'w').close()

class LiveMonitor:
    def __init__(self):
        self.last_size = 0
        self.last_mtime = 0

    def update_clone(self):
        """Update the clone file and return True if new data was found"""
        try:
            if not os.path.exists(LM_LOG):
                return False

            current_size = os.path.getsize(LM_LOG)
            current_mtime = os.path.getmtime(LM_LOG)

            # If file was rotated or truncated
            if current_size < self.last_size or current_mtime < self.last_mtime:
                self.last_size = 0

            # No new data
            if current_size == self.last_size:
                return False

            # Copy new content
            with open(LM_LOG, 'rb') as src, open(LM_CLONE, 'ab') as dst:
                src.seek(self.last_size)
                dst.write(src.read())
            
            self.last_size = current_size
            self.last_mtime = current_mtime
            return True

        except Exception as e:
            print(f"[LiveMonitor] Error updating clone: {e}")
            return False

    def process_updates(self):
        """Process updates and generate JSON if new data is available"""
        if self.update_clone():
            self.generate_json()

    def generate_json(self):
        """Generate the live_monitor.json from the clone file"""
        try:
            data = self.parse_logs(LM_LOG)
            with open(LM_JSON, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[LiveMonitor] Updated {LM_JSON}")
        except Exception as e:
            print(f"[LiveMonitor] Error generating JSON: {e}")

    def parse_logs(self, filepath: str) -> List[Dict]:
        """Parse the monitor logs into structured data"""
        result = []
        current_entry = {}
        active_functions = set()

        monitor_re = re.compile(r"\[Monitor\] (\d{2}:\d{2}:\d{2}) \| CPU: ([\d.]+)% \| Memory: *([\d.]+) MB")
        enter_re = re.compile(r"\[RealtimeMonitor\].*\[ENTER\] ([\w.]+)")

        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()

                monitor_match = monitor_re.match(line)
                if monitor_match:
                    if current_entry:
                        current_entry["active_functions"] = sorted(active_functions)
                        result.append(current_entry)
                    timestamp, cpu, mem = monitor_match.groups()
                    current_entry = {
                        "timestamp": timestamp,
                        "cpu": float(cpu),
                        "mem": float(mem),
                        "active_functions": []
                    }
                    active_functions = set()
                else:
                    enter_match = enter_re.match(line)
                    if enter_match:
                        active_functions.add(enter_match.group(1))

        if current_entry:
            current_entry["active_functions"] = sorted(active_functions)
            result.append(current_entry)

        return result

class FunctionTracker:
    def __init__(self):
        self.last_size = 0
        self.last_mtime = 0

    def update_clone(self):
        """Update the function tracker clone file"""
        try:
            if not os.path.exists(FT_LOG):
                return False

            current_size = os.path.getsize(FT_LOG)
            current_mtime = os.path.getmtime(FT_LOG)

            if current_size < self.last_size or current_mtime < self.last_mtime:
                self.last_size = 0

            if current_size == self.last_size:
                return False

            with open(FT_LOG, 'rb') as src, open(FT_CLONE, 'ab') as dst:
                src.seek(self.last_size)
                dst.write(src.read())
            
            self.last_size = current_size
            self.last_mtime = current_mtime
            return True

        except Exception as e:
            print(f"[FunctionTracker] Error updating clone: {e}")
            return False

    def process_updates(self):
        """Process function tracker updates"""
        if self.update_clone():
            self.generate_summary()

    def generate_summary(self):
        """Generate the function tracker summary"""
        try:
            summary = {}
            method = None

            with open(FT_CLONE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Method:"):
                        full = line.split("Method:")[1].strip()
                        parts = full.split(".")
                        if len(parts) >= 2:
                            key = f"{parts[-2]}.py:{parts[-1]}:0"
                            summary[key] = {
                                "calls": 0, "total_time": 0.0, "avg_cpu": 0.0, "avg_mem": 0.0,
                                "peak_cpu": 0.0, "peak_mem": 0.0
                            }
                            method = key
                    elif method and ":" in line:
                        k, v = map(str.strip, line.split(":", 1))
                        try:
                            if k.lower() == "calls":
                                summary[method]["calls"] = int(v)
                            elif k.lower().startswith("total cpu time"):
                                summary[method]["total_time"] = float(v.split()[0])
                            elif k.lower().startswith("avg cpu"):
                                summary[method]["avg_cpu"] = float(v.strip('%'))
                            elif k.lower().startswith("avg memory"):
                                summary[method]["avg_mem"] = float(v.strip(' MB'))
                            elif k.lower().startswith("peak cpu"):
                                summary[method]["peak_cpu"] = float(v.strip('%'))
                            elif k.lower().startswith("peak memory"):
                                summary[method]["peak_mem"] = float(v.strip(' MB'))
                        except:
                            continue

            with open(FT_SUMMARY_JSON, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"[FunctionTracker] Updated {FT_SUMMARY_JSON}")

        except Exception as e:
            print(f"[FunctionTracker] Error generating summary: {e}")

def monitor_live_updates():
    """Monitor live updates for both systems"""
    live_monitor = LiveMonitor()
    function_tracker = FunctionTracker()
    
    while True:
        live_monitor.process_updates()
        function_tracker.process_updates()
        time.sleep(0.1)  # Check every 100ms for updates

def start_monitors():
    """Start all monitoring threads"""
    threading.Thread(target=monitor_live_updates, daemon=True).start()

def run_java(java_class: str):
    """Run the Java process"""
    cmd = ["java", "-javaagent:JavaProfiler.jar", "-cp", ".", java_class]
    print(f"[Runner] Running Java class: {java_class}")
    subprocess.run(cmd)
    print("[Runner] Java process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="java_class", default="MultiFunctionDemo", 
                       help="Java class name to execute")
    args = parser.parse_args()

    # Clear existing files
    for f in [FT_CLONE, LM_CLONE, FT_JSON, LM_JSON, FT_SUMMARY_JSON]:
        if os.path.exists(f):
            os.remove(f)
    
    ensure_files_exist()
    start_monitors()
    run_java(args.java_class)
    print("[Runner] Monitoring complete.")