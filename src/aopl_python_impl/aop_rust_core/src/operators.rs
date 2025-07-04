// aop_rust_core/src/operators.rs

use super::aop_value::AoPValue;
use num_bigint::BigInt;
use num_traits::{One, Zero};
use std::collections::HashMap;
use std::ops::{Add, Mul, Neg, Sub};

impl Add for &AoPValue {
    type Output = AoPValue;
    fn add(self, other: &AoPValue) -> AoPValue {
        // Ensure bases are compatible for a meaningful operation.
        if self.base != other.base {
            // In a real application, you might return a Result<_, Error>
            // For now, we'll panic as this represents a logical error.
            panic!("Cannot add AoPValues with different bases.");
        }

        // Case 1: If both have a coefficient of 1, we can just merge the polynomials.
        // This is the most common and efficient path for expressions like 'a + b'.
        if self.coeff.is_one() && other.coeff.is_one() {
            let mut new_poly = self.poly.clone();
            for (exp, coeff) in &other.poly {
                *new_poly.entry(exp.clone()).or_default() += coeff;
            }
            let mut result = AoPValue::_new_internal(BigInt::one(), new_poly, self.base);
            result._simplify();
            return result;
        }

        // Case 2: General case involving coefficients, e.g., 2*(a) + 3*(b).
        // We must first "distribute" the coefficients into their respective polynomials.
        // An AoPValue like `C * {exp: coeff}` is equivalent to `{exp: C * coeff}`
        // if we set the outer coefficient to 1.
        let mut new_poly = HashMap::new();

        // Distribute self.coeff into self.poly
        for (exp, p_coeff) in &self.poly {
            *new_poly.entry(exp.clone()).or_default() += &self.coeff * p_coeff;
        }
        // Distribute other.coeff into other.poly
        for (exp, p_coeff) in &other.poly {
            *new_poly.entry(exp.clone()).or_default() += &other.coeff * p_coeff;
        }

        let mut result = AoPValue::_new_internal(BigInt::one(), new_poly, self.base);
        result._simplify();
        result
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
