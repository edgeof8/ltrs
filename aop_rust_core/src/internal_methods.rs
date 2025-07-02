// aop_rust_core/src/internal_methods.rs

use super::aop_value::AoPValue;
// KARATSUBA_THRESHOLD is not used here, so the import is removed.
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
        let mut dirty = true;

        while dirty {
            dirty = false;
            let mut carries: HashMap<BigInt, BigInt> = HashMap::new();

            let mut sorted_exps: Vec<_> = self.poly.keys().cloned().collect();
            sorted_exps.sort_unstable();

            for exp in sorted_exps {
                if let Some(coeff) = self.poly.get(&exp).cloned() {
                    if coeff >= base_bigint {
                        let (new_carry, remainder) = coeff.div_mod_floor(&base_bigint);

                        if remainder.is_zero() {
                            self.poly.remove(&exp);
                        } else {
                            self.poly.insert(exp.clone(), remainder);
                        }

                        if !new_carry.is_zero() {
                            let next_exp = exp + 1;
                            *carries.entry(next_exp).or_default() += new_carry;
                            dirty = true;
                        }
                    }
                }
            }

            for (exp, carry_val) in carries {
                *self.poly.entry(exp).or_default() += carry_val;
            }
        }

        if self.poly.is_empty() {
            self.is_negative = false;
        }
    }

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
        all_exps.sort_unstable();
        all_exps.dedup();

        for exp in all_exps.iter().rev() {
            let self_coeff = self.poly.get(exp).unwrap_or(&zero);
            let other_coeff = other.poly.get(exp).unwrap_or(&zero);
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
                    *self.poly.entry(exp + 1).or_default() -= borrows_needed;
                }
            }
        }
        self.poly.retain(|_, v| !v.is_zero());
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

    pub fn _split_at_midpoint_custom(&self, m: &BigInt) -> (Self, Self) {
        let mut low_poly = HashMap::new();
        let mut high_poly = HashMap::new();
        for (exp, coeff) in &self.poly {
            if exp < m {
                low_poly.insert(exp.clone(), coeff.clone());
            } else {
                high_poly.insert(exp - m, coeff.clone());
            }
        }
        (
            Self::_new_internal(low_poly, self.base, self.is_negative),
            Self::_new_internal(high_poly, self.base, self.is_negative),
        )
    }

    pub fn _karatsuba_mul(&self, other: &Self) -> Self {
        if self.poly.len() < 2 || other.poly.len() < 2 {
            return self._dense_mul(other);
        }
        let m = (self
            .poly
            .keys()
            .max()
            .cloned()
            .unwrap_or_default()
            .max(other.poly.keys().max().cloned().unwrap_or_default())
            / 2)
            + 1;
        let (b, a) = self._split_at_midpoint_custom(&m);
        let (d, c) = other._split_at_midpoint_custom(&m);
        let z2 = &a * &c;
        let z0 = &b * &d;
        let a_plus_b = &a + &b;
        let c_plus_d = &c + &d;
        let z1_intermediate = &a_plus_b * &c_plus_d;
        let z1 = z1_intermediate - &z2 - &z0;
        let term_z2_shifted_poly = z2.poly.into_iter().map(|(e, c)| (e + &m + &m, c));
        let term_z1_shifted_poly = z1.poly.into_iter().map(|(e, c)| (e + &m, c));
        let mut result_poly = z0.poly;
        result_poly.extend(term_z1_shifted_poly);
        result_poly.extend(term_z2_shifted_poly);
        let mut result = Self::_new_internal(
            result_poly,
            self.base,
            self.is_negative != other.is_negative,
        );
        result._simplify();
        result
    }
}
