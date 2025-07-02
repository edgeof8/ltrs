// aop_rust_core/src/operators.rs

use super::aop_value::AoPValue;
use super::KARATSUBA_THRESHOLD; // Keep for future Karatsuba re-introduction
use num_bigint::BigInt;
use std::ops::{Add, Mul, Sub};

impl<'a, 'b> Add<&'b AoPValue> for &'a AoPValue {
    type Output = AoPValue;
    fn add(self, other: &'b AoPValue) -> AoPValue {
        let mut new_poly = self.poly.clone();
        for (e, c) in &other.poly {
            *new_poly.entry(e.clone()).or_default() += c;
        }
        let mut result = AoPValue::_new_internal(new_poly, self.base, self.is_negative);
        result._simplify();
        result
    }
}

impl<'a, 'b> Sub<&'b AoPValue> for &'a AoPValue {
    type Output = AoPValue;
    fn sub(self, other: &'b AoPValue) -> AoPValue {
        let mut new_poly = self.poly.clone();
        for (e, c) in &other.poly {
            *new_poly.entry(e.clone()).or_default() -= c;
        }
        let mut result = AoPValue::_new_internal(new_poly, self.base, self.is_negative);
        result._handle_neg_coeffs();
        result._simplify();
        result
    }
}

impl Sub<AoPValue> for AoPValue {
    type Output = AoPValue;
    fn sub(self, other: AoPValue) -> AoPValue {
        &self - &other
    }
}
impl Sub<&AoPValue> for AoPValue {
    type Output = AoPValue;
    fn sub(self, other: &AoPValue) -> AoPValue {
        &self - other
    }
}

// --- NEW INTELLIGENT DISPATCHER FOR MULTIPLICATION ---
impl<'a, 'b> Mul<&'b AoPValue> for &'a AoPValue {
    type Output = AoPValue;
    fn mul(self, other: &'b AoPValue) -> AoPValue {
        // --- TRAILING ZERO SHORTCUT (Ported from your Python logic) ---
        let self_zeros = self._get_trailing_zeros();
        let other_zeros = other._get_trailing_zeros();

        // This shortcut is the key to performance in exponentiation.
        if self_zeros > BigInt::from(0) || other_zeros > BigInt::from(0) {
            let self_head = self._strip_trailing_zeros(&self_zeros);
            let other_head = other._strip_trailing_zeros(&other_zeros);

            // Recursively call mul on the "heads"
            let result_head = &self_head * &other_head;

            // Stitch result back together by adding the exponents
            let total_zeros = self_zeros + other_zeros;
            let final_poly = result_head
                .poly
                .into_iter()
                .map(|(e, c)| (e + &total_zeros, c))
                .collect();
            // We create the final value without simplifying, as the head is already simplified.
            return AoPValue::_new_internal(final_poly, self.base, result_head.is_negative);
        }

        // For now, only use dense multiplication. Karatsuba can be added back later if needed.
        self._dense_mul(other)
    }
}
