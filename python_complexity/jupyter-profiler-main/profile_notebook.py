import nbformat
import time
import traceback
import psutil
import re
import io
import os
import json
import matplotlib
from line_profiler import LineProfiler
from contextlib import redirect_stdout

# Set matplotlib to use the 'Agg' backend to suppress plot popups
matplotlib.use('Agg')

def wrap_notebook_cells_into_function(notebook_path):
    with open(notebook_path, encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    func_name = 'run_notebook_function'
    wrapped_lines = [f"def {func_name}():"]

    cell_line_mapping = {}
    current_line_num = 2  # Start from line 2 (after function def)

    for cell_idx, cell in enumerate(nb.cells):
        if cell.cell_type != 'code':
            continue

        cell_source_lines = cell.source.splitlines()
        cell_line_mapping[cell_idx] = {}

        if cell_idx > 0:
            wrapped_lines.append(f"    # Cell {cell_idx} separator")
            current_line_num += 1

        for i, line in enumerate(cell_source_lines):
            if line.strip():
                wrapped_lines.append(f"    {line}")
                cell_line_mapping[cell_idx][current_line_num] = {
                    "original_line": i + 1,
                    "code": line.strip()
                }
                current_line_num += 1

    wrapped_code = '\n'.join(wrapped_lines)

    # Write wrapped function to a .py file
    output_path = notebook_path.replace('.ipynb', '_wrapped.py')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(wrapped_code)
    print(f"Wrapped function saved to {output_path}")

    return wrapped_code, func_name, cell_line_mapping

def classify_cell(cell_data):
    total_time = cell_data["total_time"]
    total_hits = cell_data["total_hits"]
    lines = cell_data["lines"]

    avg_time_per_hit = (total_time / total_hits * 1e6) if total_hits else 0  # µs
    percent_runtime = cell_data.get("percent_time", 0)

    if percent_runtime > 30:
        return "Performance-Critical"
    elif avg_time_per_hit > 1e3:  # >1ms per hit
        return "CPU-Intensive"
    elif total_hits > 1e4 and avg_time_per_hit < 100:
        return "Loop-Intensive"

    # More robust loop and I/O detection
    loop_patterns = [
        r'\bfor\b', r'\bwhile\b', r'iteritems\s*\(', r'itertuples\s*\(', r'iterrows\s*\(',
        r'np\.nditer', r'enumerate\s*\(', r'range\s*\(', r'zip\s*\(', r'list\s*\(', r'dict\s*\('
    ]
    io_patterns = [
        r'pd\.read_\w*', r'np\.load', r'np\.save', r'pickle\.', r'open\s*\(', r'h5py\.File',
        r'csv\.reader', r'csv\.writer', r'json\.load', r'json\.dump', r'os\.listdir', r'os\.walk',
        r'shutil\.', r'glob\.glob', r'pathlib\.Path', r'with open', r'fileinput\.input', r'sqlite3\.connect'
    ]

    loop_found = False
    io_found = False
    for line_info in lines.values():
        code = line_info.get("code", "").lower()
        for pattern in io_patterns:
            if re.search(pattern, code):
                io_found = True
        for pattern in loop_patterns:
            if re.search(pattern, code):
                loop_found = True

    if io_found:
        return "I/O-Intensive"
    if loop_found and avg_time_per_hit > 1e4:
        return "Loop-Intensive"

    return "Normal"

def profile_notebook_with_line_profiler(notebook_path):
    wrapped_code, func_name, cell_line_mapping = wrap_notebook_cells_into_function(notebook_path)

    profiler = LineProfiler()
    global_ns = {}
    profile_data = {
        "metadata": {
            "notebook_path": notebook_path,
            "profile_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "function_name": func_name
        },
        "cells": {},
        "summary": {}
    }

    try:
        exec(wrapped_code, global_ns)

        if func_name not in global_ns:
            raise ValueError(f"Function {func_name} not found")

        # Memory tracking wrapper
        def wrapped_func():
            process = psutil.Process()
            mem_before = process.memory_info().rss / (1024 * 1024)
            result = global_ns[func_name]()
            mem_after = process.memory_info().rss / (1024 * 1024)
            return result, mem_after - mem_before

        profiler.add_function(global_ns[func_name])
        profiler.enable_by_count()

        start_time = time.time()
        _, memory_delta = wrapped_func()
        elapsed_time = time.time() - start_time

        profiler.disable_by_count()

        profile_data["summary"] = {
            "total_execution_time_seconds": elapsed_time,
            "memory_used_mb": memory_delta,
            "peak_memory_mb": psutil.Process().memory_info().rss / (1024 * 1024)
        }

        # Suppress output and redirect profiler stats
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            profiler.print_stats()

        # Initialize cells
        for cell_idx in cell_line_mapping:
            profile_data["cells"][str(cell_idx)] = {
                "lines": {},
                "total_time": 0,
                "total_hits": 0
            }

        # Parse profiler output
        for line in buffer.getvalue().splitlines():
            match = re.match(r"^\s*(\d+)\s+(\d+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+(.*)", line)
            if match:
                traced_line = int(match.group(1))
                hits = int(match.group(2))
                time_val = float(match.group(3))
                time_per_hit = float(match.group(4))
                percent = float(match.group(5))
                for cell_idx, lines in cell_line_mapping.items():
                    if traced_line in lines:
                        orig_line = str(lines[traced_line]["original_line"])
                        cell_data = profile_data["cells"][str(cell_idx)]

                        cell_data["lines"][orig_line] = {
                            "code": lines[traced_line]["code"],
                            "hits": hits,
                            "time": time_val,
                            "time_per_hit": time_per_hit,
                            "percent": 0.0  # will adjust later
                        }
                        cell_data["total_time"] += time_val
                        cell_data["total_hits"] += hits
                        break

        total_time_all = sum(cell["total_time"] for cell in profile_data["cells"].values())

        for cell_idx, cell in profile_data["cells"].items():
            total_cell_time = cell["total_time"]
            if total_cell_time > 0:
                for line_data in cell["lines"].values():
                    line_data["percent"] = (line_data["time"] / total_cell_time) * 100
            else:
                for line_data in cell["lines"].values():
                    line_data["percent"] = 0.0

            cell["percent_time"] = (total_cell_time / total_time_all * 100) if total_time_all > 0 else 0
            cell["classification"] = classify_cell(cell)

        output_path = os.path.abspath(notebook_path.replace('.ipynb', '_profile.json'))
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2)
        print(f"Profile saved to {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        profile_data["error"] = str(e)
        error_path = notebook_path.replace('.ipynb', '_profile_error.json')
        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", help="Path to .ipynb file")
    args = parser.parse_args()
    profile_notebook_with_line_profiler(args.notebook)
