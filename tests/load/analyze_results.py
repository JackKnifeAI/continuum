#!/usr/bin/env python3
"""
Load Test Results Analyzer

Analyzes Locust CSV output and generates summary reports.

Usage:
    python analyze_results.py results/load_test_20251206_120000_stats.csv
"""

import sys
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class EndpointStats:
    """Statistics for a single endpoint."""
    name: str
    requests: int
    failures: int
    avg_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    rps: float

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.requests == 0:
            return 0.0
        return (self.failures / self.requests) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return 100 - self.error_rate


def parse_csv(csv_path: Path) -> List[EndpointStats]:
    """Parse Locust stats CSV file."""
    stats = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip aggregated rows
            if row['Name'] == 'Aggregated':
                continue

            stats.append(EndpointStats(
                name=row['Name'],
                requests=int(row['Request Count']),
                failures=int(row['Failure Count']),
                avg_ms=float(row['Average Response Time']),
                min_ms=float(row['Min Response Time']),
                max_ms=float(row['Max Response Time']),
                p50_ms=float(row['Median Response Time']),
                p95_ms=float(row.get('95%', 0) or 0),
                p99_ms=float(row.get('99%', 0) or 0),
                rps=float(row['Requests/s']),
            ))

    return stats


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_summary(stats: List[EndpointStats]):
    """Print summary statistics."""
    print_header("OVERALL SUMMARY")

    total_requests = sum(s.requests for s in stats)
    total_failures = sum(s.failures for s in stats)
    avg_rps = sum(s.rps for s in stats)
    avg_response = sum(s.avg_ms * s.requests for s in stats) / total_requests if total_requests > 0 else 0

    print(f"\nTotal Requests:    {total_requests:,}")
    print(f"Total Failures:    {total_failures:,}")
    print(f"Error Rate:        {(total_failures/total_requests*100) if total_requests > 0 else 0:.2f}%")
    print(f"Success Rate:      {((total_requests-total_failures)/total_requests*100) if total_requests > 0 else 0:.2f}%")
    print(f"Avg Response:      {avg_response:.2f}ms")
    print(f"Total RPS:         {avg_rps:.2f}")
    print(f"Total RPM:         {avg_rps * 60:.0f}")


def print_endpoint_breakdown(stats: List[EndpointStats]):
    """Print per-endpoint breakdown."""
    print_header("ENDPOINT BREAKDOWN")

    # Sort by request count
    stats_sorted = sorted(stats, key=lambda s: s.requests, reverse=True)

    print(f"\n{'Endpoint':<40} {'Requests':>10} {'Errors':>8} {'Avg':>8} {'P95':>8} {'P99':>8} {'RPS':>8}")
    print("-" * 100)

    for stat in stats_sorted:
        error_marker = "⚠" if stat.error_rate > 1 else " "
        print(f"{stat.name[:40]:<40} {stat.requests:>10,} {error_marker}{stat.failures:>7,} "
              f"{stat.avg_ms:>7.0f}ms {stat.p95_ms:>7.0f}ms {stat.p99_ms:>7.0f}ms {stat.rps:>7.1f}")


def print_performance_analysis(stats: List[EndpointStats]):
    """Analyze performance against targets."""
    print_header("PERFORMANCE ANALYSIS")

    # Targets from config
    targets = {
        "p95_ms": 200,
        "p99_ms": 500,
        "error_rate": 1.0,
    }

    print("\nChecking against targets:")
    print(f"  Target P95: <{targets['p95_ms']}ms")
    print(f"  Target P99: <{targets['p99_ms']}ms")
    print(f"  Target Error Rate: <{targets['error_rate']}%")

    # Calculate weighted averages
    total_requests = sum(s.requests for s in stats)
    weighted_p95 = sum(s.p95_ms * s.requests for s in stats) / total_requests if total_requests > 0 else 0
    weighted_p99 = sum(s.p99_ms * s.requests for s in stats) / total_requests if total_requests > 0 else 0
    total_error_rate = sum(s.failures for s in stats) / total_requests * 100 if total_requests > 0 else 0

    print(f"\nActual Performance:")
    print(f"  P95: {weighted_p95:.0f}ms {'✓' if weighted_p95 <= targets['p95_ms'] else '✗'}")
    print(f"  P99: {weighted_p99:.0f}ms {'✓' if weighted_p99 <= targets['p99_ms'] else '✗'}")
    print(f"  Error Rate: {total_error_rate:.2f}% {'✓' if total_error_rate <= targets['error_rate'] else '✗'}")

    # Identify problem endpoints
    slow_endpoints = [s for s in stats if s.p95_ms > targets['p95_ms']]
    error_endpoints = [s for s in stats if s.error_rate > targets['error_rate']]

    if slow_endpoints:
        print(f"\n⚠ Slow Endpoints (P95 >{targets['p95_ms']}ms):")
        for stat in sorted(slow_endpoints, key=lambda s: s.p95_ms, reverse=True):
            print(f"  - {stat.name}: {stat.p95_ms:.0f}ms (P95)")

    if error_endpoints:
        print(f"\n⚠ High Error Rate Endpoints (>{targets['error_rate']}%):")
        for stat in sorted(error_endpoints, key=lambda s: s.error_rate, reverse=True):
            print(f"  - {stat.name}: {stat.error_rate:.2f}% ({stat.failures}/{stat.requests})")


def print_top_endpoints(stats: List[EndpointStats]):
    """Print top endpoints by various metrics."""
    print_header("TOP ENDPOINTS")

    # Top 5 by requests
    print("\n📊 Most Requested:")
    for i, stat in enumerate(sorted(stats, key=lambda s: s.requests, reverse=True)[:5], 1):
        print(f"  {i}. {stat.name}: {stat.requests:,} requests ({stat.rps:.1f} RPS)")

    # Top 5 slowest (by P95)
    print("\n🐌 Slowest (P95):")
    for i, stat in enumerate(sorted(stats, key=lambda s: s.p95_ms, reverse=True)[:5], 1):
        print(f"  {i}. {stat.name}: {stat.p95_ms:.0f}ms (P95)")

    # Top 5 by error rate
    print("\n⚠️  Highest Error Rate:")
    error_stats = [s for s in stats if s.failures > 0]
    for i, stat in enumerate(sorted(error_stats, key=lambda s: s.error_rate, reverse=True)[:5], 1):
        print(f"  {i}. {stat.name}: {stat.error_rate:.2f}% ({stat.failures}/{stat.requests})")


def print_recommendations(stats: List[EndpointStats]):
    """Print optimization recommendations."""
    print_header("RECOMMENDATIONS")

    total_requests = sum(s.requests for s in stats)
    total_error_rate = sum(s.failures for s in stats) / total_requests * 100 if total_requests > 0 else 0

    recommendations = []

    # Check overall error rate
    if total_error_rate > 5:
        recommendations.append("🔴 CRITICAL: Error rate >5%. System may be overloaded or misconfigured.")
        recommendations.append("   - Check API server logs")
        recommendations.append("   - Verify database connections")
        recommendations.append("   - Review resource limits (CPU, memory, connections)")
    elif total_error_rate > 1:
        recommendations.append("🟡 WARNING: Error rate >1%. Some requests are failing.")
        recommendations.append("   - Review error logs for patterns")
        recommendations.append("   - Consider scaling horizontally")

    # Check slow endpoints
    slow_endpoints = [s for s in stats if s.p95_ms > 200]
    if slow_endpoints:
        recommendations.append(f"\n🟡 {len(slow_endpoints)} endpoints have P95 >200ms:")
        for stat in sorted(slow_endpoints, key=lambda s: s.p95_ms, reverse=True)[:3]:
            recommendations.append(f"   - {stat.name}: {stat.p95_ms:.0f}ms")
        recommendations.append("   Consider:")
        recommendations.append("   - Adding database indexes")
        recommendations.append("   - Enabling caching")
        recommendations.append("   - Optimizing queries")

    # Check throughput
    total_rps = sum(s.rps for s in stats)
    target_rps = 50000 / 60  # 50k RPM = 833 RPS
    if total_rps < target_rps * 0.8:
        recommendations.append(f"\n🟡 Throughput below target: {total_rps:.0f} RPS < {target_rps:.0f} RPS")
        recommendations.append("   Consider:")
        recommendations.append("   - Scaling API servers")
        recommendations.append("   - Optimizing database queries")
        recommendations.append("   - Using connection pooling")

    if not recommendations:
        recommendations.append("✅ All metrics within acceptable ranges!")
        recommendations.append("   - P95 latency acceptable")
        recommendations.append("   - Error rate acceptable")
        recommendations.append("   - Throughput on target")

    for rec in recommendations:
        print(rec)


def main():
    """Main analysis function."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <path_to_stats.csv>")
        print("\nExample:")
        print("  python analyze_results.py results/load_test_20251206_120000_stats.csv")
        sys.exit(1)

    csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("  CONTINUUM LOAD TEST ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing: {csv_path.name}")

    # Parse CSV
    stats = parse_csv(csv_path)

    if not stats:
        print("\nNo data found in CSV file")
        sys.exit(1)

    # Print all sections
    print_summary(stats)
    print_endpoint_breakdown(stats)
    print_top_endpoints(stats)
    print_performance_analysis(stats)
    print_recommendations(stats)

    print("\n" + "=" * 80)
    print("  Analysis complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
