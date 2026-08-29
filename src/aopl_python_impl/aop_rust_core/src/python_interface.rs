// aop_rust_core/src/python_interface.rs

use super::aop_value::AoPValue;
use super::exponent_map::int_to_key_rust;
use num_bigint::{BigInt, Sign};
use num_integer::Integer;
use num_traits::{One, Signed, ToPrimitive, Zero};
use pyo3::prelude::*;
use std::collections::HashMap;
use std::ops::Neg;

impl AoPValue {
    pub fn from_numerical_internal(n: BigInt, base: u32) -> AoPValue {
        if n.is_zero() {
            return AoPValue::_new_internal(BigInt::zero(), HashMap::new(), base);
        }
        if n.abs() < BigInt::from(base) {
            return AoPValue::_new_internal(n, HashMap::new(), base);
        }
        let coeff = if n.is_negative() {
            -BigInt::one()
        } else {
            BigInt::one()
        };
        let mut n_abs = n.abs();
        let base_bigint = BigInt::from(base);
        let mut poly = HashMap::new();
        let mut exp = BigInt::zero();
        while n_abs > BigInt::zero() {
            let (new_n, remainder) = n_abs.div_mod_floor(&base_bigint);
            if !remainder.is_zero() {
                poly.insert(exp.clone(), remainder);
            }
            n_abs = new_n;
            exp += 1;
        }
        AoPValue::_new_internal(coeff, poly, base)
    }

    pub fn to_numerical(&self) -> BigInt {
        if self.poly.is_empty() {
            return self.coeff.clone();
        }
        let mut total = BigInt::zero();
        let base_bigint = BigInt::from(self.base);
        for (exp, poly_coeff) in &self.poly {
            total += poly_coeff * base_bigint.pow(exp.to_u32().unwrap_or(0));
        }
        total * &self.coeff
    }
}

#[pymethods]
impl AoPValue {
    #[new]
    #[pyo3(signature = (poly_str_keys = None, base = 10, coeff = None))]
    pub fn new(
        poly_str_keys: Option<HashMap<String, BigInt>>,
        base: u32,
        coeff: Option<BigInt>,
    ) -> Self {
        let final_coeff = coeff.unwrap_or_else(BigInt::one);
        let poly = poly_str_keys
            .unwrap_or_default()
            .iter()
            .filter_map(|(k, v)| k.parse::<BigInt>().ok().map(|exp| (exp, v.clone())))
            .collect();
        let mut val = Self::_new_internal(final_coeff, poly, base);
        val._simplify();
        val
    }

    #[staticmethod]
    pub fn from_number(n: &PyAny, base: u32) -> PyResult<Self> {
        let n_bigint: BigInt = n.extract()?;
        Ok(AoPValue::from_numerical_internal(n_bigint, base))
    }

    #[pyo3(name = "to_numerical")]
    pub fn py_to_numerical(&self) -> BigInt {
        self.to_numerical()
    }

    pub fn get_poly(&self) -> HashMap<String, BigInt> {
        self.poly
            .iter()
            .map(|(e, c)| (e.to_string(), c.clone()))
            .collect()
    }

    pub fn __repr__(&self) -> String {
        let coeff_part = match self.coeff.sign() {
            Sign::NoSign => return "AoP(0)".to_string(),
            Sign::Plus if self.coeff.is_one() => "".to_string(),
            Sign::Minus if self.coeff == -BigInt::one() => "-".to_string(),
            _ => format!("{} * ", self.coeff),
        };
        if self.poly.is_empty() {
            return format!("AoP({})", self.coeff);
        }
        let mut parts: Vec<_> = self.poly.iter().collect();
        parts.sort_by_key(|(e, _)| (*e).clone());
        parts.reverse();
        let poly_str = parts
            .iter()
            .map(|(e, c)| {
                let key = int_to_key_rust(e);
                if **c == BigInt::one() {
                    key
                } else {
                    format!("{}*{}", c, key)
                }
            })
            .collect::<Vec<_>>()
            .join(" + ");

        format!("AoP({}{})", coeff_part, poly_str)
    }

    pub fn __add__(&self, other: &Self) -> Self {
        self + other
    }
    pub fn __sub__(&self, other: &Self) -> Self {
        self - other
    }
    pub fn __mul__(&self, other: &Self) -> Self {
        self * other
    }
    pub fn __truediv__(&self, other: &Self) -> PyResult<Self> {
        self.divide(other)
    }
    pub fn __neg__(&self) -> Self {
        self.neg()
    }

    pub fn divide(&self, other: &Self) -> PyResult<Self> {
        match self.divide_poly(other) {
            Ok(value) => Ok(value),
            Err(crate::internal_methods::PolyDivError::DivisionByZero) => Err(
                pyo3::exceptions::PyValueError::new_err("Division by zero."),
            ),
            Err(crate::internal_methods::PolyDivError::DoesNotDivide) => Err(
                pyo3::exceptions::PyValueError::new_err("Polynomial does not divide evenly."),
            ),
            Err(crate::internal_methods::PolyDivError::DifferentBases) => {
                Err(pyo3::exceptions::PyValueError::new_err(
                    "Cannot divide AoPValues with different bases.",
                ))
            }
        }
    }

    fn __pow__(&self, other: &Self, _modulo: Option<&PyAny>) -> PyResult<Self> {
        self.power(other)
    }

    pub fn power(&self, exp_val: &Self) -> PyResult<Self> {
        // --- PURE SYMBOLIC PATH ---
        if self.coeff.is_one() && self.poly.len() == 1 {
            if let Some((base_exp, poly_coeff)) = self.poly.iter().next() {
                if poly_coeff.is_one() {
                    let e1_as_aop = AoPValue::from_numerical_internal(base_exp.clone(), self.base);
                    let new_exp_aop = &e1_as_aop * exp_val;
                    let final_exponent = new_exp_aop.to_numerical();
                    let final_poly = HashMap::from([(final_exponent, BigInt::one())]);
                    return Ok(AoPValue::_new_internal(
                        BigInt::one(),
                        final_poly,
                        self.base,
                    ));
                }
            }
        }

        // --- FALLBACK PATH ---
        let n = exp_val.to_numerical();
        if n.is_zero() {
            return Ok(AoPValue::from_numerical_internal(BigInt::one(), self.base));
        }
        if n.is_one() {
            return Ok(self.clone());
        }
        if n < BigInt::zero() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Negative exponents are not supported.",
            ));
        }
        let n_u32 = match n.to_u32() {
            Some(val) => val,
            None => {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "Exponent is too large for this operation.",
                ))
            }
        };

        let new_coeff = self.coeff.pow(n_u32);
        let result_poly = if !self.poly.is_empty() {
            crate::multinomial::expand_multinomial(&self.poly, n_u32)
        } else {
            HashMap::new()
        };

        let mut final_result = AoPValue::_new_internal(new_coeff, result_poly, self.base);
        final_result._simplify();
        Ok(final_result)
    }

    #[staticmethod]
    pub fn int_to_key(exp_str: &str) -> PyResult<String> {
        let exp_num = exp_str.parse::<BigInt>().map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Invalid exponent string: {}", e))
        })?;
        Ok(int_to_key_rust(&exp_num))
    }
}
