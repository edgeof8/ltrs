// aop_rust_core/src/operators.rs

use super::aop_value::{AoPValue, CoeffData, SymbolicCoefficientPy};
use num_bigint::BigInt;
use num_traits::One;
use std::collections::HashMap;
use std::ops::{Add, Mul, Neg, Sub};

// This helper now takes the Py-wrapped struct
fn coeff_to_bigint(sc: &SymbolicCoefficientPy) -> BigInt {
    // We match on the internal `data` field
    match &sc.data {
        CoeffData::Literal(value) => value.clone(),
        CoeffData::Power { .. } => {
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

        let new_coeff = SymbolicCoefficientPy {
            data: CoeffData::Literal(BigInt::one()),
        };
        AoPValue::_new_internal(new_coeff, new_poly, self.base)
    }
}

impl Neg for &AoPValue {
    type Output = AoPValue;
    fn neg(self) -> AoPValue {
        let neg_coeff_data = match &self.coeff.data {
            CoeffData::Literal(value) => CoeffData::Literal(-value),
            CoeffData::Power { .. } => panic!("Cannot negate a symbolic power coefficient."),
        };
        let new_coeff = SymbolicCoefficientPy {
            data: neg_coeff_data,
        };
        AoPValue::_new_internal(new_coeff, self.poly.clone(), self.base)
    }
}

impl Mul for &AoPValue {
    type Output = AoPValue;
    fn mul(self, other: &AoPValue) -> AoPValue {
        let c1 = coeff_to_bigint(&self.coeff);
        let c2 = coeff_to_bigint(&other.coeff);
        let new_coeff = SymbolicCoefficientPy {
            data: CoeffData::Literal(c1 * c2),
        };

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
