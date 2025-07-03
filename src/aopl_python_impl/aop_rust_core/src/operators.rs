// aop_rust_core/src/operators.rs

use super::aop_value::{AoPValue, SymbolicCoefficient};
use num_bigint::BigInt;
use num_traits::{One, Zero};
use std::collections::HashMap;
use std::ops::{Add, Mul, Neg, Sub};

fn coeff_to_bigint(sc: &SymbolicCoefficient) -> BigInt {
    match sc {
        SymbolicCoefficient::Literal { value } => value.clone(),
        SymbolicCoefficient::Power { .. } => {
            panic!("Cannot perform arithmetic with a symbolic power coefficient.");
        }
    }
}

impl Add for &AoPValue {
    type Output = AoPValue;
    fn add(self, other: &AoPValue) -> AoPValue {
        let c1 = coeff_to_bigint(&self.coeff);
        let c2 = coeff_to_bigint(&other.coeff);
        let self_scaled: HashMap<_, _> = self
            .poly
            .iter()
            .map(|(e, c)| (e.clone(), c * &c1))
            .collect();
        let other_scaled: HashMap<_, _> = other
            .poly
            .iter()
            .map(|(e, c)| (e.clone(), c * &c2))
            .collect();
        let mut new_poly = self_scaled;
        for (e, c) in other_scaled {
            *new_poly.entry(e).or_default() += c;
        }
        AoPValue::_new_internal(
            SymbolicCoefficient::Literal {
                value: BigInt::one(),
            },
            new_poly,
            self.base,
        )
    }
}

impl Neg for &AoPValue {
    type Output = AoPValue;
    fn neg(self) -> AoPValue {
        let neg_coeff = match &self.coeff {
            SymbolicCoefficient::Literal { value } => {
                SymbolicCoefficient::Literal { value: -value }
            }
            SymbolicCoefficient::Power { .. } => {
                panic!("Cannot negate a symbolic power coefficient.")
            }
        };
        AoPValue::_new_internal(neg_coeff, self.poly.clone(), self.base)
    }
}

impl Mul for &AoPValue {
    type Output = AoPValue;
    fn mul(self, other: &AoPValue) -> AoPValue {
        let c1 = coeff_to_bigint(&self.coeff);
        let c2 = coeff_to_bigint(&other.coeff);
        let new_coeff = SymbolicCoefficient::Literal { value: c1 * c2 };
        let new_poly = AoPValue::_mul_poly_raw(&self.poly, &other.poly);
        AoPValue::_new_internal(new_coeff, new_poly, self.base)
    }
}

// Boilerplate
impl Sub for &AoPValue {
    type Output = AoPValue;
    fn sub(self, other: &AoPValue) -> AoPValue {
        self.add(&other.neg())
    }
}
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
