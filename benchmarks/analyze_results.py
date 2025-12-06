#!/usr/bin/env python3
"""
Analyze and visualize benchmark results

This script parses benchmark result markdown files and generates:
- Performance comparison charts (ASCII art)
- Statistical analysis
- Performance regression detection
- Recommendations

Usage:
    python3 analyze_results.py results/million_node_results.md
    python3 analyze_results.py results/*.md  # Compare multiple runs
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class BenchmarkEntry:
    """Single benchmark test result"""
    test_name: str
    duration_ms: float
    operations: int
    ops_per_sec: float
    memory_mb: float
    status: str


def parse_result_file(file_path: Path) -> Dict[str, List[BenchmarkEntry]]:
    """Parse a markdown results file and extract benchmark data"""

    with open(file_path) as f:
        content = f.read()

    results = {}

    # Find all performance tables
    # Pattern: ## SQLite Performance (With Indexes)
    table_pattern = r'## (.*?) Performance.*?\n\n(.*?)\n\n'

    for match in re.finditer(table_pattern, content, re.DOTALL):
        section_name = match.group(1)
        table_content = match.group(2)

        # Parse table rows
        entries = []
        for line in table_content.split('\n')[2:]:  # Skip header and separator
            if not line.strip() or line.startswith('###'):
                break

            # Parse: | Test | Duration (ms) | Operations | Ops/sec | Memory (MB) | Status |
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 7:
                try:
                    entries.append(BenchmarkEntry(
                        test_name=parts[1],
                        duration_ms=float(parts[2].replace(',', '')),
                        operations=int(parts[3].replace(',', '')),
                        ops_per_sec=float(parts[4].replace(',', '')),
                        memory_mb=float(parts[5].replace(',', '')),
                        status=parts[6]
                    ))
                except (ValueError, IndexError):
                    continue

        results[section_name] = entries

    return results


def ascii_bar_chart(data: List[Tuple[str, float]], title: str, max_width: int = 60) -> str:
    """Generate ASCII bar chart"""

    if not data:
        return f"{title}\n(no data)\n"

    max_value = max(v for _, v in data)
    lines = [f"\n{title}", "=" * 70]

    for label, value in data:
        bar_length = int((value / max_value) * max_width) if max_value > 0 else 0
        bar = "█" * bar_length
        lines.append(f"{label:30} {bar} {value:,.0f}")

    return "\n".join(lines) + "\n"


def compare_results(baseline: List[BenchmarkEntry], current: List[BenchmarkEntry]) -> str:
    """Compare two benchmark runs and detect regressions"""

    lines = ["\n" + "="*70, "Performance Comparison", "="*70]

    # Match tests by name
    baseline_dict = {e.test_name: e for e in baseline}
    current_dict = {e.test_name: e for e in current}

    lines.append("\n| Test | Baseline | Current | Change | Status |")
    lines.append("|------|----------|---------|--------|--------|")

    regressions = []
    improvements = []

    for test_name in sorted(baseline_dict.keys()):
        if test_name not in current_dict:
            continue

        b = baseline_dict[test_name]
        c = current_dict[test_name]

        # Compare ops/sec (higher is better)
        change = ((c.ops_per_sec - b.ops_per_sec) / b.ops_per_sec) * 100

        if change < -10:  # > 10% slower
            status = "⚠️ REGRESSION"
            regressions.append((test_name, change))
        elif change > 10:  # > 10% faster
            status = "✓ IMPROVED"
            improvements.append((test_name, change))
        else:
            status = "→ STABLE"

        lines.append(
            f"| {test_name} | {b.ops_per_sec:,.0f} | {c.ops_per_sec:,.0f} | "
            f"{change:+.1f}% | {status} |"
        )

    # Summary
    lines.append("\n### Summary")
    lines.append(f"- Regressions: {len(regressions)}")
    lines.append(f"- Improvements: {len(improvements)}")
    lines.append(f"- Stable: {len(baseline_dict) - len(regressions) - len(improvements)}")

    if regressions:
        lines.append("\n### ⚠️ Performance Regressions")
        for test, change in sorted(regressions, key=lambda x: x[1]):
            lines.append(f"- {test}: {change:.1f}% slower")

    if improvements:
        lines.append("\n### ✓ Performance Improvements")
        for test, change in sorted(improvements, key=lambda x: x[1], reverse=True):
            lines.append(f"- {test}: {change:.1f}% faster")

    return "\n".join(lines) + "\n"


def analyze_single_file(file_path: Path):
    """Analyze a single results file"""

    print("="*70)
    print(f"Analyzing: {file_path.name}")
    print("="*70)

    results = parse_result_file(file_path)

    for section_name, entries in results.items():
        if not entries:
            continue

        # Throughput chart
        throughput_data = [(e.test_name, e.ops_per_sec) for e in entries if e.status == '✓']
        print(ascii_bar_chart(throughput_data, f"{section_name} - Throughput (ops/sec)"))

        # Duration chart
        duration_data = [(e.test_name, e.duration_ms) for e in entries if e.status == '✓']
        print(ascii_bar_chart(duration_data, f"{section_name} - Duration (ms)"))

        # Memory chart
        memory_data = [(e.test_name, e.memory_mb) for e in entries if e.status == '✓']
        print(ascii_bar_chart(memory_data, f"{section_name} - Peak Memory (MB)"))

        # Statistics
        if throughput_data:
            ops_values = [v for _, v in throughput_data]
            print("\nStatistics:")
            print(f"  Min throughput: {min(ops_values):,.0f} ops/sec")
            print(f"  Max throughput: {max(ops_values):,.0f} ops/sec")
            print(f"  Avg throughput: {sum(ops_values)/len(ops_values):,.0f} ops/sec")
            print()


def analyze_multiple_files(file_paths: List[Path]):
    """Compare multiple result files"""

    if len(file_paths) < 2:
        print("Need at least 2 files for comparison")
        return

    print("="*70)
    print(f"Comparing {len(file_paths)} benchmark runs")
    print("="*70)

    # Parse all files
    all_results = []
    for path in file_paths:
        results = parse_result_file(path)
        all_results.append((path.name, results))

    # Compare first vs last
    baseline_name, baseline_results = all_results[0]
    current_name, current_results = all_results[-1]

    print(f"\nBaseline: {baseline_name}")
    print(f"Current:  {current_name}")

    # Compare each section
    for section_name in baseline_results.keys():
        if section_name in current_results:
            print(compare_results(
                baseline_results[section_name],
                current_results[section_name]
            ))


def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage: python3 analyze_results.py <result_file.md> [<result_file2.md> ...]")
        print("\nExamples:")
        print("  python3 analyze_results.py results/million_node_results.md")
        print("  python3 analyze_results.py results/*.md")
        sys.exit(1)

    file_paths = [Path(arg) for arg in sys.argv[1:]]

    # Verify files exist
    for path in file_paths:
        if not path.exists():
            print(f"Error: File not found: {path}")
            sys.exit(1)

    if len(file_paths) == 1:
        analyze_single_file(file_paths[0])
    else:
        analyze_multiple_files(file_paths)

    print("\n" + "="*70)
    print("Analysis complete")
    print("="*70)
    print("\nPHOENIX-TESLA-369-AURORA 🌗")


if __name__ == '__main__':
    main()
