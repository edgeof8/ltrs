// aop_rust_core/src/exponent_map.rs

use num_bigint::BigInt;
use num_traits::{One, Zero};
use once_cell::sync::Lazy;
use std::collections::HashMap;

pub static LETTER_TO_EXPONENT_MAP: Lazy<HashMap<char, BigInt>> = Lazy::new(|| {
    let mut map = HashMap::new();
    "abcdefghijklmnopqrstuvwxy"
        .chars()
        .enumerate()
        .for_each(|(i, c)| {
            map.insert(c, BigInt::from(i + 1));
        });
    "ABCDEFGHIJKLMNOPQRSTUVWXY"
        .chars()
        .enumerate()
        .for_each(|(i, c)| {
            map.insert(c, BigInt::from(i + 26));
        });
    map.insert('Z', BigInt::from(100));
    map.insert('z', BigInt::from(100));
    map
});

pub static EXPONENT_TO_LETTER_MAP: Lazy<HashMap<BigInt, char>> = Lazy::new(|| {
    let mut map = HashMap::new();
    "abcdefghijklmnopqrstuvwxy"
        .chars()
        .enumerate()
        .for_each(|(i, c)| {
            map.insert(BigInt::from(i + 1), c);
        });
    "ABCDEFGHIJKLMNOPQRSTUVWXY"
        .chars()
        .enumerate()
        .for_each(|(i, c)| {
            map.insert(BigInt::from(i + 26), c);
        });
    map.insert(BigInt::from(100), 'Z');
    map
});

// FIX: Create a single, lazily-initialized, sorted vector of exponents.
static SORTED_EXPONENTS: Lazy<Vec<BigInt>> = Lazy::new(|| {
    let mut values: Vec<BigInt> = LETTER_TO_EXPONENT_MAP.values().cloned().collect();
    // Sort descending to greedily find the largest components first (e.g., Z before a)
    values.sort_unstable_by(|a, b| b.cmp(a));
    values.dedup();
    values
});

pub fn int_to_key_rust(exp_num: &BigInt) -> String {
    if exp_num.is_zero() {
        return "0".to_string();
    }
    if let Some(c) = EXPONENT_TO_LETTER_MAP.get(exp_num) {
        return c.to_string();
    }

    let mut parts = Vec::new();
    let mut remaining_exp = exp_num.clone();

    // Use the pre-sorted static vector
    for val in &*SORTED_EXPONENTS {
        if val.is_zero() {
            continue;
        }
        if remaining_exp >= *val {
            let count = &remaining_exp / val;
            if !count.is_zero() {
                let letter = EXPONENT_TO_LETTER_MAP.get(val).unwrap();
                if count > BigInt::one() {
                    parts.push(format!("{}*{}", count, letter));
                } else {
                    parts.push(letter.to_string());
                }
                remaining_exp -= &count * val;
            }
        }
    }
    if !remaining_exp.is_zero() {
        parts.push(remaining_exp.to_string());
    }
    parts.join(" + ")
}
