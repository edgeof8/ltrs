// aop_rust_core/src/operators.rs

use super::aop_value::AoPValue;
use num_bigint::BigInt;
use num_traits::Zero;
use std::collections::HashMap;
use std::ops::{Add, Mul, Neg, Sub};

impl Add for &AoPValue {
    type Output = AoPValue;
    fn add(self, other: &AoPValue) -> AoPValue {
        debug_assert_eq!(
            self.base, other.base,
            "add of AoPValues with different bases (Python must check first)"
        );
        if self.base != other.base {
            // Mixed bases are a logic error. Python pymethods reject them with PyErr
            // before calling this. Returning the left operand would hide bugs.
            panic!("Cannot add AoPValues with different bases.");
        }

        // Distribute k·p and m·q into Z[X], add, then carry.
        // Empty poly is the constant coeff (so 1 + a is a + 1, and cancelling
        // spikes become 0 rather than the constant 1).
        let mut new_poly = self.as_distributed_poly();
        for (exp, coeff) in other.as_distributed_poly() {
            *new_poly.entry(exp).or_default() += coeff;
        }
        AoPValue::from_distributed_poly(new_poly, self.base)
    }
}

impl Sub for &AoPValue {
    type Output = AoPValue;
    fn sub(self, other: &AoPValue) -> AoPValue {
        self + &other.neg()
    }
}

impl Neg for &AoPValue {
    type Output = AoPValue;
    fn neg(self) -> AoPValue {
        AoPValue::_new_internal(-&self.coeff, self.poly.clone(), self.base)
    }
}

impl Mul for &AoPValue {
    type Output = AoPValue;
    fn mul(self, other: &AoPValue) -> AoPValue {
        debug_assert_eq!(self.base, other.base, "mul of AoPValues with different bases");
        if self.base != other.base {
            panic!("Cannot multiply AoPValues with different bases.");
        }
        let new_coeff = &self.coeff * &other.coeff;
        if new_coeff.is_zero() {
            return AoPValue::_new_internal(BigInt::zero(), HashMap::new(), self.base);
        }
        let new_poly = AoPValue::_mul_poly_raw(&self.poly, &other.poly);
        let mut result = AoPValue::_new_internal(new_coeff, new_poly, self.base);
        result._simplify();
        result
    }
}

// Implement traits for owned values
impl Add for AoPValue {
    type Output = AoPValue;
    fn add(self, other: AoPValue) -> AoPValue {
        &self + &other
    }
}
impl Sub for AoPValue {
    type Output = AoPValue;
    fn sub(self, other: AoPValue) -> AoPValue {
        &self - &other
    }
}
impl Mul for AoPValue {
    type Output = AoPValue;
    fn mul(self, other: AoPValue) -> AoPValue {
        &self * &other
    }
}
impl Neg for AoPValue {
    type Output = AoPValue;
    fn neg(self) -> AoPValue {
        <&AoPValue>::neg(&self)
    }
}
