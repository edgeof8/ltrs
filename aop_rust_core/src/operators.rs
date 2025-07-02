// aop_rust_core/src/operators.rs

use super::aop_value::AoPValue;
use super::KARATSUBA_THRESHOLD;
// HashMap is not directly used here, so the import is removed.
use std::ops::{Add, Mul, Sub};

impl<'a, 'b> Add<&'b AoPValue> for &'a AoPValue {
    type Output = AoPValue;
    fn add(self, other: &'b AoPValue) -> AoPValue {
        let mut new_poly = self.poly.clone();
        for (e, c) in &other.poly {
            *new_poly.entry(e.clone()).or_default() += c;
        }
        AoPValue::_new_internal(new_poly, self.base, self.is_negative)
    }
}

impl<'a, 'b> Sub<&'b AoPValue> for &'a AoPValue {
    type Output = AoPValue;
    fn sub(self, other: &'b AoPValue) -> AoPValue {
        let mut new_poly = self.poly.clone();
        for (e, c) in &other.poly {
            *new_poly.entry(e.clone()).or_default() -= c;
        }
        AoPValue::_new_internal(new_poly, self.base, self.is_negative)
    }
}

// Add blanket implementations to allow moving/borrowing flexibility
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

impl<'a, 'b> Mul<&'b AoPValue> for &'a AoPValue {
    type Output = AoPValue;
    fn mul(self, other: &'b AoPValue) -> AoPValue {
        if self.poly.len() > KARATSUBA_THRESHOLD && other.poly.len() > KARATSUBA_THRESHOLD {
            self._karatsuba_mul(other)
        } else {
            self._dense_mul(other)
        }
    }
}
