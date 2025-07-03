// aop_rust_core/src/internal_methods.rs

use super::aop_value::AoPValue;
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use rayon::prelude::*;
use std::collections::HashMap;

impl AoPValue {
    pub fn _new_internal(coeff: BigInt, poly: HashMap<BigInt, BigInt>, base: u32) -> Self {
        let poly_filtered = poly.into_iter().filter(|(_, c)| !c.is_zero()).collect();
        Self {
            coeff,
            poly: poly_filtered,
            base,
        }
    }

    pub fn _simplify(&mut self) {
        if self.poly.is_empty() {
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
                if coeff.abs() >= base_bigint {
                    let (new_carry, remainder) = coeff.clone().div_mod_floor(&base_bigint);
                    *coeff = remainder;
                    if !new_carry.is_zero() {
                        let next_exp = exp.clone() + BigInt::one();
                        let entry = self.poly.entry(next_exp.clone()).or_default();
                        *entry += new_carry;
                        if !sorted_exps.contains(&next_exp) {
                            sorted_exps.push(next_exp);
                            sorted_exps.sort_unstable();
                        }
                    }
                }
            }
            i += 1;
        }
        self.poly.retain(|_, v| !v.is_zero());
    }

    pub fn _handle_neg_coeffs(&mut self) {
        // This logic remains largely the same as it operates on the polynomial's BigInts
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

    pub fn _mul_poly_raw(
        p1: &HashMap<BigInt, BigInt>,
        p2: &HashMap<BigInt, BigInt>,
    ) -> HashMap<BigInt, BigInt> {
        if p1.is_empty() {
            return p2.clone();
        }
        if p2.is_empty() {
            return p1.clone();
        }
        p1.par_iter()
            .flat_map(|(e1, c1)| p2.par_iter().map(move |(e2, c2)| (e1 + e2, c1 * c2)))
            .fold(HashMap::new, |mut map, (exp, coeff)| {
                *map.entry(exp).or_default() += coeff;
                map
            })
            .reduce(HashMap::new, |mut map1, map2| {
                for (exp, coeff) in map2 {
                    *map1.entry(exp).or_default() += coeff;
                }
                map1
            })
    }
}
