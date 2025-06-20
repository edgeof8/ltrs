import subprocess
import json
from datetime import datetime

def analyze_pattern(output):
    """Analyze AoP output for fractal patterns"""
    pattern_score = 0.0

    # Pattern detection heuristics
    if '^' in output:
        pattern_score += 0.3
    if output.count('(') > 1:
        pattern_score += 0.4
    if any(char.isupper() for char in output):
        pattern_score += 0.3

    return min(1.0, pattern_score)

def run_experiments():
    results = []
    BASES = [2, 10, 2.71828]  # Including base e
    DEPTHS = range(3, 7)       # Nesting levels 3-6
    LETTERS = ['a', 'b', 'c', 'j']  # Representative letters

    for base in BASES:
        for depth in DEPTHS:
            for letter in LETTERS:
                # Build expression: letter^letter^...^letter
                expr = letter + '^' * (depth-1) + letter

                try:
                    cmd = [
                        'python', '-m', 'src.aopl_python_impl.aop_calculator_cli',
                        f'"{expr}"', '--base', str(base)
                    ]
                    result = subprocess.run(
                        ' '.join(cmd),
                        capture_output=True,
                        text=True,
                        shell=True
                    )
                    output = result.stdout.strip()
                    pattern_score = analyze_pattern(output)

                    results.append({
                        'base': base,
                        'depth': depth,
                        'letter': letter,
                        'expression': expr,
                        'output': output,
                        'pattern_score': pattern_score,
                        'timestamp': datetime.now().isoformat()
                    })

                except Exception as e:
                    print(f"Error processing {expr} in base {base}: {str(e)}")

    return results

if __name__ == "__main__":
    experiment_results = run_experiments()

    # Save results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"research/experiment_results/pattern_test_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(experiment_results, f, indent=2)

    print(f"Saved {len(experiment_results)} test results to {filename}")
