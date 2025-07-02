// aop_rust_core/src/internal_methods.rs

use super::aop_value::AoPValue;
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use std::collections::HashMap;

impl AoPValue {
    pub fn _new_internal(poly: HashMap<BigInt, BigInt>, base: u32, is_negative: bool) -> Self {
        let poly_filtered = poly.into_iter().filter(|(_, c)| !c.is_zero()).collect();
        Self {
            poly: poly_filtered,
            base,
            is_negative,
        }
    }

    pub fn _simplify(&mut self) {
        if self.poly.is_empty() {
            self.is_negative = false;
            return;
        }

        self._handle_neg_coeffs();

        let base_bigint = BigInt::from(self.base);
        let mut sorted_exps: Vec<_> = self.poly.keys().cloned().collect();
        sorted_exps.sort_unstable();

        let mut i = 0;
        while i < sorted_exps.len() {
            let exp = sorted_exps[i].clone();
            if let Some(coeff) = self.poly.get_mut(&exp) {
                if *coeff >= base_bigint {
                    let (new_carry, remainder) = coeff.clone().div_mod_floor(&base_bigint);

                    if remainder.is_zero() {
                        // We will remove it after the loop to avoid borrow checker issues.
                        *coeff = BigInt::zero();
                    } else {
                        *coeff = remainder;
                    }

                    if !new_carry.is_zero() {
                        // --- THIS IS THE FIX ---
                        // We must clone `exp` before moving it into the addition.
                        let next_exp = exp.clone() + BigInt::one();
                        let entry = self.poly.entry(next_exp.clone()).or_default();
                        *entry += new_carry;

                        if let Err(pos) = sorted_exps.binary_search(&next_exp) {
                            sorted_exps.insert(pos, next_exp);
                        }
                    }
                }
            }
            i += 1;
        }

        // Clean up any zero-coefficient entries that might have been created
        self.poly.retain(|_, v| !v.is_zero());

        if self.poly.is_empty() {
            self.is_negative = false;
        }
    }

    // ... (the rest of the internal methods are correct and do not need to change) ...
    pub fn _compare_magnitude(&self, other: &Self) -> i8 {
        let self_max_exp = self
            .poly
            .keys()
            .max()
            .cloned()
            .unwrap_or_else(|| BigInt::from(-1));
        let other_max_exp = other
            .poly
            .keys()
            .max()
            .cloned()
            .unwrap_or_else(|| BigInt::from(-1));
        if self_max_exp > other_max_exp {
            return 1;
        }
        if other_max_exp > self_max_exp {
            return -1;
        }
        let zero = BigInt::zero();
        let mut all_exps: Vec<_> = self.poly.keys().chain(other.poly.keys()).cloned().collect();
        all_exps.sort_unstable_by(|a, b| b.cmp(a));
        all_exps.dedup();
        for exp in all_exps {
            let self_coeff = self.poly.get(&exp).unwrap_or(&zero);
            let other_coeff = other.poly.get(&exp).unwrap_or(&zero);
            if self_coeff > other_coeff {
                return 1;
            }
            if other_coeff > self_coeff {
                return -1;
            }
        }
        0
    }

    pub fn _handle_neg_coeffs(&mut self) {
        if self.poly.values().all(|c| !c.is_negative()) {
            return;
        }
        let mut sorted_exps: Vec<_> = self.poly.keys().cloned().collect();
        sorted_exps.sort_unstable();
        let base_bigint = BigInt::from(self.base);
        let one = BigInt::one();
        for exp in sorted_exps {
            if let Some(coeff_val) = self.poly.get(&exp) {
                if coeff_val.is_negative() {
                    let coeff_val = coeff_val.clone();
                    let borrows_needed = (coeff_val.abs() + &base_bigint - &one) / &base_bigint;
                    *self.poly.entry(exp.clone()).or_default() += &borrows_needed * &base_bigint;
                    *self.poly.entry(exp.clone() + BigInt::one()).or_default() -= borrows_needed;
                }
            }
        }
        self.poly.retain(|_, v| !v.is_zero());
    }

    pub fn _get_trailing_zeros(&self) -> BigInt {
        self.poly.keys().min().cloned().unwrap_or_default()
    }

    pub fn _strip_trailing_zeros(&self, zero_count: &BigInt) -> Self {
        if zero_count.is_zero() {
            return self.clone();
        }
        let new_poly = self
            .poly
            .iter()
            .map(|(e, c)| (e - zero_count, c.clone()))
            .collect();
        Self::_new_internal(new_poly, self.base, self.is_negative)
    }

    pub fn _dense_mul(&self, other: &Self) -> Self {
        if self.poly.is_empty() || other.poly.is_empty() {
            return Self::_new_internal(HashMap::new(), self.base, false);
        }
        let mut new_poly = HashMap::new();
        for (e1, c1) in &self.poly {
            for (e2, c2) in &other.poly {
                *new_poly.entry(e1 + e2).or_default() += c1 * c2;
            }
        }
        let mut result =
            Self::_new_internal(new_poly, self.base, self.is_negative != other.is_negative);
        result._simplify();
        result
    }
}
