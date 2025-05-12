import sys
import os
import psutil
import threading
import time
import json
from datetime import datetime
from collections import defaultdict

class FunctionProfiler:
    def __init__(self, target_script, sample_interval=0.5, realtime_json_file="realtime_monitor.json", stats_json_file="function_statistics.json"):
        self.target_script = os.path.abspath(target_script)
        self.sample_interval = sample_interval
        self.process = psutil.Process(os.getpid())
        self.active_functions = set()
        self.call_counts = defaultdict(int)
        self.function_times = defaultdict(list)
        self.call_stack = []
        self.lock = threading.Lock()
        self.per_second_log = []
        self.stop_event = threading.Event()

        # Function-level CPU/Memory samples
        self.function_cpu_samples = defaultdict(list)
        self.function_mem_samples = defaultdict(list)

        # Real-time JSON logging
        self.realtime_json_file = realtime_json_file
        self.realtime_data = []

        # Final statistics JSON file
        self.stats_json_file = stats_json_file

    def start_monitoring(self):
        last_print_time = time.time()
        samples = []

        while not self.stop_event.is_set():
            now = time.time()
            cpu = self.process.cpu_percent(interval=None)
            mem = self.process.memory_info().rss / (1024 * 1024)  # MB

            with self.lock:
                current_active = list(self.active_functions) if self.active_functions else ['<main>']
                samples.append({
                    'timestamp': now,
                    'cpu': cpu,
                    'mem': mem,
                    'active_functions': current_active
                })

                for func_id in current_active:
                    self.function_cpu_samples[func_id].append(cpu)
                    self.function_mem_samples[func_id].append(mem)

            time.sleep(self.sample_interval)

            if now - last_print_time >= 1.0:
                avg_cpu = sum(sample['cpu'] for sample in samples) / len(samples)
                avg_mem = sum(sample['mem'] for sample in samples) / len(samples)
                active_funcs = set()
                for sample in samples:
                    active_funcs.update(sample['active_functions'])

                timestamp = datetime.now().strftime('%H:%M:%S')

                per_second_entry = {
                    'timestamp': timestamp,
                    'cpu': avg_cpu,
                    'mem': avg_mem,
                    'active_functions': sorted(list(active_funcs))
                }
                self.per_second_log.append(per_second_entry)

                try:
                    with open(self.realtime_json_file, 'w') as f:
                        json.dump(self.realtime_data, f, indent=2)
                except Exception as e:
                    print(f"Error writing to realtime JSON: {e}")

                self.realtime_data.append(per_second_entry)
                samples.clear()
                last_print_time = now

    def trace_calls(self, frame, event, arg):
        filename = os.path.abspath(frame.f_code.co_filename)
        if filename != self.target_script:
            return

        if event == 'call':
            self.function_enter(frame)
        elif event == 'return':
            self.function_exit(frame)

        return self.trace_calls

    def function_enter(self, frame):
        func_name = frame.f_code.co_name
        if func_name == '<module>':
            func_name = '<main>'
        lineno = frame.f_code.co_firstlineno
        func_id = f"{os.path.basename(self.target_script)}:{func_name}:{lineno}"

        now = time.time()

        with self.lock:
            self.call_stack.append((func_id, now))
            self.active_functions.add(func_id)
            self.call_counts[func_id] += 1

    def function_exit(self, frame):
        func_name = frame.f_code.co_name
        if func_name == '<module>':
            func_name = '<main>'
        lineno = frame.f_code.co_firstlineno
        func_id = f"{os.path.basename(self.target_script)}:{func_name}:{lineno}"

        now = time.time()

        with self.lock:
            if self.call_stack and self.call_stack[-1][0] == func_id:
                _, enter_time = self.call_stack.pop()
                elapsed = now - enter_time
                self.function_times[func_id].append(elapsed)

            if func_id in self.active_functions:
                self.active_functions.remove(func_id)

    def get_aggregated_stats(self):
        aggregated = {}

        for func_id, times in self.function_times.items():
            if '<main>' in func_id:
                continue
            calls = self.call_counts.get(func_id, 0)
            total_time = sum(times)

            cpu_samples = self.function_cpu_samples.get(func_id, [])
            mem_samples = self.function_mem_samples.get(func_id, [])

            avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
            avg_mem = sum(mem_samples) / len(mem_samples) if mem_samples else 0

            peak_cpu = max(cpu_samples) if cpu_samples else 0
            peak_mem = max(mem_samples) if mem_samples else 0

            aggregated[func_id] = {
                'calls': calls,
                'total_time': total_time,
                'avg_cpu': avg_cpu,
                'avg_mem': avg_mem,
                'peak_cpu': peak_cpu,
                'peak_mem': peak_mem
            }

        return aggregated

    def start(self):
        monitoring_thread = threading.Thread(target=self.start_monitoring)
        monitoring_thread.start()

        sys.settrace(self.trace_calls)

        globals_dict = {"__name__": "__main__"}
        try:
            with open(self.target_script, 'rb') as f:
                exec(compile(f.read(), self.target_script, 'exec'), globals_dict)
        finally:
            self.stop_event.set()
            monitoring_thread.join()
            sys.settrace(None)

    def display_results(self):
        aggregated = self.get_aggregated_stats()
        print("\nFunction Statistics:")
        print("{:<50} {:<10} {:<12} {:<10} {:<10} {:<10} {:<10}".format(
            'Function', 'Calls', 'Total Time(s)', 'Avg CPU(%)', 'Avg Mem(MB)', 'Peak CPU(%)', 'Peak Mem(MB)'
        ))
        print("-" * 120)

        for func_id, data in sorted(aggregated.items(), key=lambda x: -x[1]['total_time']):
            print("{:<50} {:<10} {:<12.4f} {:<10.2f} {:<10.2f} {:<10.2f} {:<10.2f}".format(
                func_id, data['calls'], data['total_time'],
                data['avg_cpu'], data['avg_mem'], data['peak_cpu'], data['peak_mem']
            ))

        print("\nResource Usage Per Second:")
        print("{:<10} {:<8} {:<10} {:<50}".format('Time', 'CPU (%)', 'Memory (MB)', 'Active Functions'))
        print("-" * 80)

        for log in self.per_second_log:
            print("{:<10} {:<8.1f} {:<10.1f} {:<50}".format(
                log['timestamp'], log['cpu'], log['mem'], ", ".join(sorted(log['active_functions']))
            ))

        try:
            with open(self.stats_json_file, 'w') as f:
                json.dump(aggregated, f, indent=2)
        except Exception as e:
            print(f"Error writing to stats JSON: {e}")

# =====================================
# Main
# =====================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <script_to_profile.py>")
        sys.exit(1)

    target_script = sys.argv[1]

    if not os.path.isfile(target_script):
        print(f"Error: '{target_script}' does not exist!")
        sys.exit(1)

    profiler = FunctionProfiler(target_script, sample_interval=0.5)
    profiler.start()
    profiler.display_results()
