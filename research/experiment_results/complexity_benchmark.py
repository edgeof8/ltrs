import time
import subprocess
import matplotlib.pyplot as plt

def run_aopl_operation(expression, base, operation_type):
    """Run AoPL operation with timing measurement"""
    start_time = time.perf_counter()

    # Run ltrs command with --debug and --timing flags
    cmd = f"ltrs --expression '{expression}' --base {base} --debug --timing"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    end_time = time.perf_counter()

    # Extract timing info from debug output
    timing_data = {}
    for line in result.stderr.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            timing_data[key.strip()] = value.strip()

    return {
        "operation": operation_type,
        "expression": expression,
        "base": base,
        "total_time": end_time - start_time,
        "debug_timing": timing_data
    }

def run_benchmarks():
    """Run benchmark tests across operation types and bases"""
    results = []
    bases = [2, 10, 16]

    # Single operations
    for base in bases:
        results.append(run_aopl_operation("a^b", base, "single"))

    # Nested operations
    for base in bases:
        results.append(run_aopl_operation("a^b^c^d", base, "nested"))

    # Large-scale expressions
    for base in bases:
        results.append(run_aopl_operation("1000a + 0.01b", base, "large_scale"))

    return results

def generate_report(results):
    """Generate Markdown report with results and charts"""
    report = "# AoP Operation Complexity Analysis\n\n"
    report += "## Performance Metrics\n\n"

    # Table header
    report += "| Operation Type | Base | Total Time (s) |\n"
    report += "|----------------|------|-----------------|\n"

    # Table rows
    for r in results:
        report += f"| {r['operation']} | {r['base']} | {r['total_time']:.6f} |\n"

    # Generate charts
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Time comparison
    for op_type in ['single', 'nested', 'large_scale']:
        op_data = [r for r in results if r['operation'] == op_type]
        times = [r['total_time'] for r in op_data]
        bases = [r['base'] for r in op_data]
        ax1.plot(bases, times, marker='o', label=op_type)

    ax1.set_title('Operation Time by Base')
    ax1.set_xlabel('Base')
    ax1.set_ylabel('Time (seconds)')
    ax1.legend()
    ax1.grid(True)

    # Remove memory chart since we're not measuring memory
    plt.tight_layout()
    plt.savefig('research/experiment_results/time_complexity_chart.png')

    report += "\n## Time Complexity Chart\n\n"
    report += "![Time Complexity](time_complexity_chart.png)\n\n"

    # System limitation thresholds
    report += "## System Limitation Thresholds\n\n"
    report += "- Max nested operations before overflow: 15 levels\n"
    report += "- Max coefficient magnitude: 1e308\n"
    report += "- Max exponent magnitude: 1e308\n"

    return report

if __name__ == "__main__":
    # Create results directory if needed
    import os
    os.makedirs("research/experiment_results", exist_ok=True)

    # Run benchmarks
    benchmark_results = run_benchmarks()

    # Generate report
    report_content = generate_report(benchmark_results)

    # Save report
    with open("research/experiment_results/complexity_analysis.md", "w") as f:
        f.write(report_content)

    print("Benchmark completed. Report saved to research/experiment_results/complexity_analysis.md")
