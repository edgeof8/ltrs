// aop_rust_core/src/multinomial.rs

use num_bigint::BigInt;
use num_traits::{One, Zero};
use rayon::prelude::*;
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Instant;

// --- k-vector Generation (Recursive) ---

fn generate_k_vectors_recursive(
    m: usize,
    n: u32,
    current_k: &mut Vec<u32>,
    results: &mut Vec<Vec<u32>>,
) {
    if m == 1 {
        current_k.push(n);
        results.push(current_k.clone());
        current_k.pop(); // Backtrack
        return;
    }

    for i in 0..=n {
        current_k.push(i);
        generate_k_vectors_recursive(m - 1, n - i, current_k, results);
        current_k.pop(); // Backtrack
    }
}

fn generate_k_vectors(num_terms: usize, n: u32) -> Vec<Vec<u32>> {
    let mut results = Vec::new();
    if num_terms > 0 {
        generate_k_vectors_recursive(num_terms, n, &mut Vec::new(), &mut results);
    }
    results
}

// --- Coefficient Calculation ---

fn calculate_n_choose_k(n: u32, k: u32) -> BigInt {
    if k > n {
        return BigInt::zero();
    }
    let k = k.min(n - k);
    if k == 0 {
        return BigInt::one();
    }
    let mut res = BigInt::one();
    for i in 0..k {
        res = (res * (n as i64 - i as i64)) / (i as i64 + 1);
    }
    res
}

fn calculate_multinomial_coeff(n: u32, k_vector: &[u32]) -> BigInt {
    let mut result = BigInt::one();
    let mut current_n = n;
    // Skip the last k value as (k_m choose k_m) is always 1
    for &k in k_vector.iter().take(k_vector.len() - 1) {
        result *= calculate_n_choose_k(current_n, k);
        current_n -= k;
    }
    result
}

// --- Main Expansion Function ---

pub fn expand_multinomial(
    poly: &HashMap<BigInt, BigInt>,
    n: u32,
) -> Result<HashMap<BigInt, BigInt>, String> {
    let m = poly.len();
    if m == 0 {
        return Ok(HashMap::new());
    }

    // Sanity Check to prevent combinatorial explosion.
    // The number of k-vectors is (n + m - 1) choose (m - 1).
    let num_combinations = calculate_n_choose_k(n + m as u32 - 1, m as u32 - 1);
    if num_combinations > BigInt::from(1_000_000) {
        // Return an error string instead of panicking
        return Err(format!(
            "Multinomial expansion too complex: {} combinations exceeds limit.",
            num_combinations
        ));
    }

    let terms: Vec<_> = poly.iter().map(|(e, c)| (e.clone(), c.clone())).collect();
    let k_vectors = generate_k_vectors(m, n);
    let total_combinations = k_vectors.len();

    // --- NEW: Progress Reporting Setup ---
    let counter = AtomicUsize::new(0);
    let start_time = Instant::now();
    // Print initial status only if it's a large job
    if total_combinations > 1000 {
        eprintln!(
            "Starting multinomial expansion: {} terms to compute...",
            total_combinations
        );
    }

    // Use Rayon to process all k-vectors in parallel
    let result = k_vectors
        .into_par_iter()
        .map(|k_vec| {
            // This closure computes a single term of the final polynomial
            let multinomial_coeff = calculate_multinomial_coeff(n, &k_vec);
            let mut final_term_coeff = multinomial_coeff;
            let mut final_term_exp = BigInt::zero();

            for i in 0..m {
                let (base_exp, base_coeff) = &terms[i];
                let k = k_vec[i];
                final_term_coeff *= base_coeff.pow(k);
                final_term_exp += base_exp * k;
            }

            // --- NEW: Increment and Report Progress ---
            let count = counter.fetch_add(1, Ordering::Relaxed);
            // Print an update every 4096 iterations to avoid spamming the console
            if count > 0 && (count & 4095) == 0 {
                let elapsed = start_time.elapsed().as_secs_f32();
                let percent_done = (count as f32 / total_combinations as f32) * 100.0;
                let rate = count as f32 / elapsed;
                eprintln!(
                    "  -> Progress: {:.2}% ({}/{} terms computed) [{:.0} terms/sec]",
                    percent_done, count, total_combinations, rate
                );
            }

            (final_term_exp, final_term_coeff)
        })
        .fold(HashMap::new, |mut map, (exp, coeff)| {
            *map.entry(exp).or_default() += coeff;
            map
        })
        .reduce(HashMap::new, |mut map1, map2| {
            for (exp, coeff) in map2 {
                *map1.entry(exp).or_default() += coeff;
            }
            map1
        });

    // --- NEW: Final Report ---
    if total_combinations > 1000 {
        eprintln!(
            "Expansion complete in {:.2} seconds.",
            start_time.elapsed().as_secs_f32()
        );
    }

    Ok(result)
}
