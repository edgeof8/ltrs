// benches/aops_benchmark.rs

// FIX 1: Use direct module reference for AoPValue
use aop_value::AoPValue;

// FIX 2 & 3: Add necessary `use` statements for traits
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use num_bigint::BigInt;
use num_traits::{One, Zero}; // Import Zero and One traits
use std::collections::HashMap;

/// Helper function to create a large, dense AoPValue
fn create_large_aop_value(num_terms: usize, base: u32) -> AoPValue {
    let mut poly = HashMap::new();
    for i in 0..num_terms {
        poly.insert(BigInt::from(i), BigInt::from(i % (base as usize - 1) + 1));
    }
    AoPValue {
        poly,
        base,
        is_negative: false,
    }
}

fn bench_multiplication(c: &mut Criterion) {
    let mut group = c.benchmark_group("Multiplication");

    let small = create_large_aop_value(10, 10);
    let medium = create_large_aop_value(500, 10);
    let large = create_large_aop_value(1000, 10);

    group.bench_function("mul_small_x_small", |b| {
        b.iter(|| small.clone().__mul__(black_box(&small)))
    });

    group.bench_function("mul_medium_x_medium", |b| {
        b.iter(|| medium.clone().__mul__(black_box(&medium)))
    });

    group.bench_function("mul_large_x_large", |b| {
        b.iter(|| large.clone().__mul__(black_box(&large)))
    });

    group.finish();
}

fn bench_to_numerical(c: &mut Criterion) {
    // This is a stand-in for the actual large result.
    // We create a value with many terms to simulate a complex result.
    let large_result = create_large_aop_value(5000, 10);

    c.bench_function("to_numerical_large", |b| {
        b.iter(|| large_result.to_numerical())
    });
}

fn bench_power(c: &mut Criterion) {
    let mut group = c.benchmark_group("Power");

    // Base for the power operation: (2b+3a) -> 2*10^2 + 3*10^1 = 230
    let complex_base = AoPValue {
        poly: HashMap::from([
            (BigInt::from(2), BigInt::from(2)),
            (BigInt::from(1), BigInt::from(3)),
        ]),
        base: 10,
        is_negative: false,
    };

    // Exponent: 100
    let medium_exp = AoPValue {
        poly: HashMap::from([(BigInt::zero(), BigInt::from(100))]),
        base: 10,
        is_negative: false,
    };

    // Exponent: 5002 (your slow case)
    let large_exp = AoPValue {
        poly: HashMap::from([(BigInt::zero(), BigInt::from(5002))]),
        base: 10,
        is_negative: false,
    };

    // Exponent for symbolic test: 'b' -> 10^2
    let symbolic_exp_b = AoPValue {
        poly: HashMap::from([(BigInt::from(2), BigInt::one())]),
        base: 10,
        is_negative: false,
    };
    // Base for symbolic test: 'a' -> 10^1
    let symbolic_base_a = AoPValue {
        poly: HashMap::from([(BigInt::one(), BigInt::one())]),
        base: 10,
        is_negative: false,
    };

    group.bench_function("power_complex_base_medium_exp (230^100)", |b| {
        b.iter(|| complex_base.power(black_box(&medium_exp)))
    });

    group.bench_function("power_complex_base_large_exp (230^5002)", |b| {
        b.iter(|| complex_base.power(black_box(&large_exp)))
    });

    group.bench_function("power_symbolic_base (a^b)", |b| {
        b.iter(|| symbolic_base_a.power(black_box(&symbolic_exp_b)))
    });

    group.finish();
}

// FIX 4: Register the benchmark groups with criterion
criterion_group!(
    benches,
    bench_multiplication,
    bench_to_numerical,
    bench_power
);
criterion_main!(benches);
