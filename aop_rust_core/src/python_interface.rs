// aop_rust_core/src/python_interface.rs

use super::aop_value::AoPValue;
use super::exponent_map::int_to_key_rust; // Removed unused key_to_int_rust
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, ToPrimitive, Zero};
use pyo3::prelude::*;
use std::collections::HashMap;
use std::ops::{Add, Mul, Sub};

// --- NEW HELPER FUNCTION ---
// This private helper creates an AoPValue from a Rust BigInt, bypassing PyO3's PyAny.
fn from_bigint(n: &BigInt, base: u32) -> AoPValue {
    if n.is_zero() {
        return AoPValue::_new_internal(HashMap::new(), base, false);
    }
    let is_negative = n.is_negative();
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
    AoPValue::_new_internal(poly, base, is_negative)
}

#[pymethods]
impl AoPValue {
    #[new]
    #[pyo3(signature = (poly_str_keys = None, base = 10, is_negative = false))]
    pub fn new(
        poly_str_keys: Option<HashMap<String, BigInt>>,
        base: u32,
        is_negative: bool,
    ) -> Self {
        let poly = poly_str_keys
            .unwrap_or_default()
            .iter()
            .filter_map(|(k, v)| k.parse::<BigInt>().ok().map(|exp| (exp, v.clone())))
            .filter(|(_, v)| !v.is_zero())
            .collect();
        let mut val = Self::_new_internal(poly, base, is_negative);
        val._simplify();
        val
    }

    #[staticmethod]
    pub fn from_number(n: &PyAny, base: u32) -> PyResult<Self> {
        let n_bigint: BigInt = n.extract()?;
        // Delegate to the internal Rust-native helper function
        Ok(from_bigint(&n_bigint, base))
    }

    pub fn to_numerical(&self) -> BigInt {
        let mut total = BigInt::zero();
        let base_bigint = BigInt::from(self.base);
        for (exp, coeff) in &self.poly {
            if *exp >= BigInt::zero() {
                if let Some(e_u32) = exp.to_u32() {
                    total += coeff * base_bigint.clone().pow(e_u32);
                } else {
                    return BigInt::from(-1);
                }
            }
        }
        if self.is_negative {
            -total
        } else {
            total
        }
    }

    #[getter]
    pub fn get_poly(&self) -> HashMap<String, BigInt> {
        self.poly
            .iter()
            .map(|(e, c)| (e.to_string(), c.clone()))
            .collect()
    }

    pub fn __repr__(&self) -> String {
        let mut parts: Vec<_> = self.poly.iter().collect();
        parts.sort_by_key(|(e, _)| (*e).clone());
        parts.reverse();
        let poly_str = parts
            .iter()
            .map(|(e, c)| format!("@{}:{}", int_to_key_rust(e), c))
            .collect::<Vec<_>>()
            .join(", ");
        let sign = if self.is_negative { "-" } else { "" };
        format!(
            "AoP({}{{{}}})",
            sign,
            if poly_str.is_empty() { "0" } else { &poly_str }
        )
    }

    pub fn __add__(&self, other: &Self) -> Self {
        self.add(other)
    }

    pub fn __sub__(&self, other: &Self) -> Self {
        if self.is_negative != other.is_negative {
            let mut other_flipped = other.clone();
            other_flipped.is_negative = !other_flipped.is_negative;
            return self.__add__(&other_flipped);
        }
        let mag_cmp = self._compare_magnitude(other);
        if mag_cmp == 0 {
            return Self::_new_internal(HashMap::new(), self.base, false);
        }
        let mut result = if mag_cmp == 1 {
            self.sub(other)
        } else {
            other.sub(self)
        };
        result.is_negative = if mag_cmp == 1 {
            self.is_negative
        } else {
            !self.is_negative
        };
        result._handle_neg_coeffs();
        result._simplify();
        result
    }

    pub fn __mul__(&self, other: &Self) -> Self {
        self.mul(other)
    }

    fn __pow__(&self, other: &Self, modulo: Option<&PyAny>) -> PyResult<Self> {
        if modulo.is_some() {
            return Err(pyo3::exceptions::PyNotImplementedError::new_err(
                "Modular exponentiation is not implemented.",
            ));
        }

        if self.poly.len() == 1 {
            if let Some((exp1, coeff1)) = self.poly.iter().next() {
                if coeff1.is_one() && !self.is_negative {
                    let exp1_as_aop = from_bigint(exp1, self.base);
                    let new_exponent_aop = &exp1_as_aop * other;
                    let final_exponent_val = new_exponent_aop.to_numerical();
                    if final_exponent_val == BigInt::from(-1) {
                        return Err(pyo3::exceptions::PyValueError::new_err(
                            "Resulting exponent is too large to represent.",
                        ));
                    }
                    let new_poly = HashMap::from([(final_exponent_val, BigInt::one())]);
                    return Ok(Self::_new_internal(new_poly, self.base, false));
                }
            }
        }

        // --- CRITICAL FIX ---
        // For complex bases, attempt to flatten the exponent.
        // If it's too big (to_numerical returns -1), then this operation is unresolvable.
        let n = other.to_numerical();
        if n == BigInt::from(-1) {
            // Signal to Python that this cannot be resolved numerically.
            return Err(pyo3::exceptions::PyNotImplementedError::new_err(
                "Complex base cannot be raised to a non-numeric exponent.",
            ));
        }

        if n < BigInt::zero() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Exponent must be non-negative for complex bases.",
            ));
        }
        if n.is_zero() {
            return Ok(Self::_new_internal(
                HashMap::from([(BigInt::zero(), BigInt::one())]),
                self.base,
                false,
            ));
        }
        if n.is_one() {
            return Ok(self.clone());
        }

        let mut result = Self::_new_internal(
            HashMap::from([(BigInt::zero(), BigInt::one())]),
            self.base,
            false,
        );
        let mut current_base = self.clone();
        let mut n_rem = n;
        while n_rem > BigInt::zero() {
            if n_rem.is_odd() {
                result = &result * &current_base;
            }
            current_base = &current_base * &current_base;
            n_rem /= 2;
        }
        Ok(result)
    }
}
