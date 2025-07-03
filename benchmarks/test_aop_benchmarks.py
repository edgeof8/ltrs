# benchmarks/test_aop_benchmarks.py
import pytest
from aopl_python_impl.aop_calculator import AoP_Calculator

@pytest.fixture
def calc():
    # Use no-cache for fair benchmarking of raw computation speed
    calculator = AoP_Calculator(base=10)
    calculator.cache = None
    return calculator

def test_bench_simple_add(benchmark, calc):
    benchmark(calc.evaluate_expression, "a+b")

def test_bench_complex_mul(benchmark, calc):
    # A multiplication that can't use the trailing zero shortcut
    benchmark(calc.evaluate_expression, "(a+1)*(b+1)")

def test_bench_mul_with_shortcut(benchmark, calc):
    # A multiplication that SHOULD use the trailing zero shortcut
    benchmark(calc.evaluate_expression, "(a+b)*c")

def test_bench_power_shortcut(benchmark, calc):
    # The key test for our new symbolic power optimization
    # Before: Very Slow. After: Very Fast.
    benchmark(calc.evaluate_expression, "b^a")

def test_bench_power_fallback(benchmark, calc):
    # A test for the slower, complex base exponentiation
    # Before: Slow. After: Still slow, but that's expected.
    benchmark(calc.evaluate_expression, "(a+1)^b")

def test_bench_sub_expression_caching(benchmark):
    # This test will be much faster with the cache than without.
    # Run once to populate cache, then benchmark the second run.
    calc_with_cache = AoP_Calculator(base=10)
    expression = "(a+b+c)^2 - (a+b+c)"

    # Prime the cache if it's not already primed
    if not calc_with_cache.cache:
        calc_with_cache.evaluate_expression(expression)

    # Benchmark the cached evaluation
    benchmark(calc_with_cache.evaluate_expression, expression)
