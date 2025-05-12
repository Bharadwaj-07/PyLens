import os
import ast
import sys
import json
import math
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze
from collections import defaultdict
from vulture import Vulture

class CodeAnalyzer:
    def __init__(self):
        self.smell_counts = defaultdict(int)
        self.smell_thresholds = {
            'long_function': 30,
            'long_class': 100,
            'many_parameters': 5,
            'deep_nesting': 3,
            'many_methods': 10,
            'high_complexity': 10,
            'inconsistent_names': True,
            'dead_code': 0
        }
        self.analysis_results = {
            "projectName": "",
            "files": [],
            "summary": {
                "totalFiles": 0,
                "totalLines": 0,
                "totalClasses": 0,
                "totalFunctions": 0,
                "maintainabilityIndex": 0,
                "reusabilityScore": 0,
                "carbonFootprint": 0,
                "smells": []
            }
        }

    def analyze_directory(self, directory_path):
        self.analysis_results["projectName"] = os.path.basename(os.path.abspath(directory_path))
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory_path)
                    self.analyze_file(file_path, relative_path)

        self.calculate_project_metrics()
        self.save_results_to_json(directory_path)

    def analyze_file(self, file_path, relative_path):
        file_data = {
            "path": relative_path,
            "fileName": os.path.basename(file_path),
            "fileStats": {},
            "complexity": [],
            "smells": [],
            "maintainabilityIndex": 0,
            "ownership": defaultdict(list),
            "deadCode": []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                code = file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return

        # Analyze file stats
        try:
            raw_metrics = analyze(code)
            file_data["fileStats"] = {
                "loc": raw_metrics.loc,
                "comments": raw_metrics.comments,
                "blank": raw_metrics.blank,
                "commentRatio": raw_metrics.comments / raw_metrics.loc if raw_metrics.loc > 0 else 0
            }
        except Exception as e:
            print(f"Error in file statistics analysis for {file_path}: {e}")

        # Parse AST and build parent relationships
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                for child in ast.iter_child_nodes(node):
                    child.parent = node
        except Exception as e:
            print(f"Error parsing AST for {file_path}: {e}")
            return

        # Analyze all functions and methods
        self.analyze_functions_and_methods(file_data, tree, code)

        # Calculate maintainability index
        try:
            mi = mi_visit(code, True)
            file_data["maintainabilityIndex"] = round(mi, 2)
        except Exception as e:
            print(f"Error in maintainability index calculation for {file_path}: {e}")

        # Analyze code smells
        self.analyze_code_smells(file_data, tree)

        # Analyze dead code
        self.analyze_dead_code(file_data, tree, code, file_path)

        self.analysis_results["files"].append(file_data)

    def analyze_functions_and_methods(self, file_data, tree, code):
        """Analyze all functions and methods for complexity"""
        try:
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node)

            # Analyze standalone functions
            for func in functions:
                if not isinstance(func.parent, ast.ClassDef):
                    self.analyze_function_complexity(file_data, func, code, is_method=False)

            # Analyze class methods
            for class_node in classes:
                for node in ast.walk(class_node):
                    if isinstance(node, ast.FunctionDef):
                        self.analyze_function_complexity(file_data, node, code, is_method=True)

        except Exception as e:
            print(f"Error analyzing functions/methods: {e}")

    def analyze_function_complexity(self, file_data, func_node, code, is_method):
        """Analyze complexity of a single function/method"""
        try:
            func_code = ast.unparse(func_node)
            cc_results = cc_visit(func_code)
            if not cc_results:
                return
                
            block = cc_results[0]
            class_name = None
            if is_method:
                class_name = func_node.parent.name if hasattr(func_node, 'parent') and isinstance(func_node.parent, ast.ClassDef) else None

            complexity_data = {
                "name": block.name,
                "value": block.complexity,
                "type": "method" if is_method else "function",
                "class": class_name,
                "issues": []
            }
            
            if block.complexity > self.smell_thresholds['high_complexity']:
                complexity_data["issues"].append(f"High complexity (>{self.smell_thresholds['high_complexity']})")
                self.smell_counts['high_complexity'] += 1
            
            file_data["complexity"].append(complexity_data)

            # Track ownership
            if is_method:
                file_data["ownership"][func_node.parent.name].append(func_node.name)
            else:
                file_data["ownership"]["<global>"].append(func_node.name)

        except Exception as e:
            print(f"Error analyzing function complexity: {e}")

    def analyze_code_smells(self, file_data, tree):
        """Analyze code smells for the file with proper snake_case validation"""
        try:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_length = self._get_node_length(node)
                    if class_length > self.smell_thresholds['long_class']:
                        self.smell_counts['long_class'] += 1
                        smell = {
                            "type": "Long Class",
                            "message": f"{node.name} ({class_length} lines)",
                            "line": node.lineno
                        }
                        file_data["smells"].append(smell)
                        for comp in file_data["complexity"]:
                            if comp.get("type") == "class" and comp.get("name") == node.name:
                                comp.setdefault("issues", []).append(smell["type"])

                elif isinstance(node, ast.FunctionDef):
                    method_length = self._get_node_length(node)
                    if method_length > self.smell_thresholds['long_function']:
                        self.smell_counts['long_function'] += 1
                        smell = {
                            "type": "Long Function",
                            "message": f"{node.name}() ({method_length} lines)",
                            "line": node.lineno
                        }
                        file_data["smells"].append(smell)
                        for comp in file_data["complexity"]:
                            if comp.get("name") == node.name and (not comp.get("class") or comp.get("class") == getattr(node.parent, "name", None)):
                                comp.setdefault("issues", []).append(smell["type"])

                    if len(node.args.args) > self.smell_thresholds['many_parameters']:
                        self.smell_counts['many_parameters'] += 1
                        smell = {
                            "type": "Many Parameters",
                            "message": f"{node.name}() ({len(node.args.args)} parameters)",
                            "line": node.lineno
                        }
                        file_data["smells"].append(smell)
                        for comp in file_data["complexity"]:
                            if comp.get("name") == node.name and (not comp.get("class") or comp.get("class") == getattr(node.parent, "name", None)):
                                comp.setdefault("issues", []).append(smell["type"])

                    depth = self._get_max_nesting(node)
                    if depth > self.smell_thresholds['deep_nesting']:
                        self.smell_counts['deep_nesting'] += 1
                        smell = {
                            "type": "Deep Nesting",
                            "message": f"{node.name}() (depth {depth})",
                            "line": node.lineno
                        }
                        file_data["smells"].append(smell)
                        for comp in file_data["complexity"]:
                            if comp.get("name") == node.name and (not comp.get("class") or comp.get("class") == getattr(node.parent, "name", None)):
                                comp.setdefault("issues", []).append(smell["type"])

                    # Improved naming convention check
                    parent = getattr(node, 'parent', None)
                    name = node.name
                    
                    if isinstance(parent, ast.ClassDef):
                        # Method naming - should be snake_case
                        if not self._is_valid_snake_case(name) and not name.startswith('__'):
                            self.smell_counts['inconsistent_names'] += 1
                            smell = {
                                "type": "Inconsistent Naming",
                                "message": f"Method {name}() (should be snake_case)",
                                "line": node.lineno
                            }
                            file_data["smells"].append(smell)
                            for comp in file_data["complexity"]:
                                if comp.get("name") == name and comp.get("class") == parent.name:
                                    comp.setdefault("issues", []).append(smell["type"])
                    else:
                        # Function naming - should be snake_case
                        if not self._is_valid_snake_case(name):
                            self.smell_counts['inconsistent_names'] += 1
                            smell = {
                                "type": "Inconsistent Naming",
                                "message": f"Function {name}() (should be snake_case)",
                                "line": node.lineno
                            }
                            file_data["smells"].append(smell)
                            for comp in file_data["complexity"]:
                                if comp.get("name") == name and not comp.get("class"):
                                    comp.setdefault("issues", []).append(smell["type"])

        except Exception as e:
            print(f"Error analyzing code smells: {e}")

    def _is_valid_snake_case(self, name):
        """
        Proper snake_case validation that won't flag valid names.
        Valid snake_case: lowercase with optional underscores between words,
        doesn't start/end with underscore (unless it's a special name),
        no consecutive underscores.
        """
        if name.startswith('__') and name.endswith('__'):
            return True  # Magic methods are allowed
        
        if name == '_':
            return True  # Single underscore is allowed
        
        if '__' in name:
            return False  # No double underscores except in magic methods
            
        if name.startswith('_') or name.endswith('_'):
            return False  # No leading/trailing underscores
            
        if not name.replace('_', '').islower():
            return False  # Must be all lowercase
            
        if any(char.isdigit() for char in name) and name[0].isdigit():
            return False  # Numbers are allowed but not at start
            
        return True

    def analyze_dead_code(self, file_data, tree, code, file_path):
        """Analyze dead code using vulture"""
        try:
            vulture_analyzer = Vulture()
            vulture_analyzer.scan(code, filename=file_path)
            dead_code = vulture_analyzer.get_unused_code()

            seen = set()  # Track unique dead code entries
            if dead_code:
                for item in dead_code[:10]:  # Limit to 10 dead code items per file
                    owner = '<global>'
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name == item.name:
                            parent = getattr(node, 'parent', None)
                            if isinstance(parent, ast.ClassDef):
                                owner = parent.name
                    dead_code_str = f"{owner}.{item.name} ({item.typ})" if owner != '<global>' else f"{item.name} ({item.typ})"
                    if dead_code_str in seen:
                        continue  # Skip duplicates
                    seen.add(dead_code_str)
                    file_data["deadCode"].append(dead_code_str)
                    self.smell_counts['dead_code'] += 1

                    for comp in file_data["complexity"]:
                        if owner != '<global>':
                            if comp.get("name") == item.name and comp.get("class") == owner:
                                if "Dead Code" not in comp.setdefault("issues", []):
                                    comp["issues"].append("Dead Code")
                        else:
                            if comp.get("name") == item.name and not comp.get("class"):
                                if "Dead Code" not in comp.setdefault("issues", []):
                                    comp["issues"].append("Dead Code")

        except Exception as e:
            print(f"Error analyzing dead code: {e}")

    def calculate_project_metrics(self):
        """Calculate all project-level metrics with improved robustness"""
        total_files = len(self.analysis_results["files"])
        total_lines = sum(f["fileStats"].get("loc", 0) for f in self.analysis_results["files"])
        
        # Calculate weighted average maintainability index
        mi_values = []
        for f in self.analysis_results["files"]:
            if "maintainabilityIndex" in f:
                weight = f["fileStats"].get("loc", 1)  # Weight by file size
                mi_values.append((f["maintainabilityIndex"], weight))
        
        if mi_values:
            total_weight = sum(w for _, w in mi_values)
            avg_mi = sum(mi * w for mi, w in mi_values) / total_weight if total_weight > 0 else 0
        else:
            avg_mi = 0

        # Count classes and functions with more robust detection
        total_classes = 0
        total_functions = 0
        class_method_counts = []
        
        for file_data in self.analysis_results["files"]:
            for class_name, methods in file_data["ownership"].items():
                if class_name != "<global>":
                    total_classes += 1
                    class_method_counts.append(len(methods))
                total_functions += len(methods)

        # Enhanced reusability score calculation
        reusability_score = self.calculate_reusability_score(
            total_classes,
            total_functions,
            class_method_counts
        )

        # More sophisticated carbon footprint estimation
        carbon_footprint = self.estimate_carbon_footprint(
            total_lines,
            total_classes,
            total_functions,
            self.smell_counts
        )

        # Update summary with enhanced metrics
        self.analysis_results["summary"] = {
            "totalFiles": total_files,
            "totalLines": total_lines,
            "totalClasses": total_classes,
            "totalFunctions": total_functions,
            "maintainabilityIndex": round(avg_mi, 2),
            "reusabilityScore": round(reusability_score, 2),
            "carbonFootprint": round(carbon_footprint, 2),
            "smells": [
                {"type": "Long Functions", "count": self.smell_counts["long_function"]},
                {"type": "Long Classes", "count": self.smell_counts["long_class"]},
                {"type": "Many Parameters", "count": self.smell_counts["many_parameters"]},
                {"type": "Deep Nesting", "count": self.smell_counts["deep_nesting"]},
                {"type": "Many Methods", "count": self.smell_counts["many_methods"]},
                {"type": "High Complexity", "count": self.smell_counts["high_complexity"]},
                {"type": "Inconsistent Names", "count": self.smell_counts["inconsistent_names"]},
                {"type": "Dead Code", "count": self.smell_counts["dead_code"]}
            ]
        }

    def calculate_reusability_score(self, total_classes, total_functions, class_method_counts):
        """
        Calculate a more robust reusability score based on multiple factors:
        1. Average methods per class (lower is better)
        2. Percentage of pure functions (functions not in classes)
        """
        if total_classes == 0:
            return 0  # No classes means no OOP reusability
            
        avg_methods = sum(class_method_counts) / total_classes if class_method_counts else 0
        pure_function_ratio = (total_functions - sum(class_method_counts)) / total_functions if total_functions > 0 else 0
        
        # Score components (0-100 scale)
        method_score = max(0, 100 - (avg_methods * 5))  # Penalize many methods per class
        pure_function_score = pure_function_ratio * 50  # Reward pure functions (up to 50 points)
        
        # Combine scores with weights
        reusability_score = (method_score * 0.7) + (pure_function_score * 0.3)
        
        return min(100, max(0, reusability_score))

    def estimate_carbon_footprint(self, total_lines, total_classes, total_functions, smell_counts):
        """
        Estimate carbon footprint based on:
        1. Codebase size (lines of code)
        2. Complexity (via code smells)
        3. Maintainability issues
        """
        # Base footprint from code size (logarithmic scale)
        size_factor = math.log10(total_lines + 1) * 0.5
        
        # Complexity penalty
        complexity_penalty = (
            smell_counts['high_complexity'] * 0.1 +
            smell_counts['deep_nesting'] * 0.05 +
            smell_counts['long_function'] * 0.02
        )
        
        # Maintenance penalty
        maintenance_penalty = (
            smell_counts['long_class'] * 0.05 +
            smell_counts['many_parameters'] * 0.03 +
            smell_counts['dead_code'] * 0.01
        )
        
        # Calculate final footprint (0-10 scale)
        footprint = min(10, 
            size_factor + 
            complexity_penalty + 
            maintenance_penalty +
            (total_classes * 0.01) +  # Small penalty for more classes
            (total_functions * 0.001)  # Tiny penalty for more functions
        )
        
        return footprint

    def save_results_to_json(self, directory_path):
        output_path = os.path.join(directory_path, "complexity_report.json")
        with open(output_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        print(f"\nAnalysis results saved to: {output_path}")

    def _get_node_length(self, node):
        if hasattr(node, 'end_lineno'):
            return node.end_lineno - node.lineno + 1
        last_node = node.body[-1] if node.body else node
        return (last_node.lineno - node.lineno + 1) if hasattr(last_node, 'lineno') else 0

    def _get_max_nesting(self, node):
        max_depth = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth = sum(1 for _ in self._get_parents(child) if isinstance(_, (ast.If, ast.For, ast.While, ast.With, ast.Try)))
                max_depth = max(max_depth, depth)
        return max_depth

    def _get_parents(self, node):
        while hasattr(node, 'parent'):
            node = node.parent
            yield node


if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = input("Enter directory path to analyze: ").strip()

    analyzer = CodeAnalyzer()
    analyzer.analyze_directory(directory)