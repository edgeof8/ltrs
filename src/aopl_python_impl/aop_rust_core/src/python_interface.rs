// aop_rust_core/src/python_interface.rs

use super::aop_value::{AoPValue, SymbolicCoefficient};
use super::exponent_map::int_to_key_rust;
use super::multinomial::expand_multinomial;
use num_bigint::{BigInt, Sign};
use num_integer::Integer;
use num_traits::{One, Signed, ToPrimitive, Zero};
use pyo3::prelude::*;
use std::collections::HashMap;

fn from_bigint(n: &BigInt, base: u32) -> AoPValue {
    let coeff = SymbolicCoefficient::Literal {
        value: if n.is_negative() {
            -BigInt::one()
        } else {
            BigInt::one()
        },
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

#[pymethods]
impl AoPValue {
    #[new]
    #[pyo3(signature = (poly_str_keys = None, base = 10, coeff = None))]
    pub fn new(
        poly_str_keys: Option<HashMap<String, BigInt>>,
        base: u32,
        coeff: Option<BigInt>,
    ) -> Self {
        let final_coeff = SymbolicCoefficient::Literal {
            value: coeff.unwrap_or_else(BigInt::one),
        };
        let poly = poly_str_keys
            .unwrap_or_default()
            .into_iter()
            .filter_map(|(k, v)| k.parse::<BigInt>().ok().map(|exp| (exp, v)))
            .collect();
        Self::_new_internal(final_coeff, poly, base)
    }

    #[staticmethod]
    pub fn from_number(n: &PyAny, base: u32) -> PyResult<Self> {
        let n_bigint: BigInt = n.extract()?;
        Ok(from_bigint(&n_bigint, base))
    }

    #[staticmethod]
    #[pyo3(signature = (coeff, poly_str_keys, base))]
    fn from_state(
        coeff: SymbolicCoefficient,
        poly_str_keys: HashMap<String, BigInt>,
        base: u32,
    ) -> Self {
        let poly = poly_str_keys
            .into_iter()
            .filter_map(|(k, v)| k.parse::<BigInt>().ok().map(|exp| (exp, v)))
            .collect();
        // Directly use the provided coefficient, no need for Literal wrapping
        Self::_new_internal(coeff, poly, base)
    }

    // --- NEW: Methods to let Python inspect the coefficient ---
    #[getter]
    pub fn get_coeff_as_literal(&self) -> Option<BigInt> {
        match &self.coeff {
            SymbolicCoefficient::Literal { value } => Some(value.clone()),
            _ => None,
        }
    }

    #[getter]
    pub fn get_coeff_as_power(&self) -> Option<(BigInt, BigInt)> {
        match &self.coeff {
            SymbolicCoefficient::Power { base, exponent } => Some((base.clone(), exponent.clone())),
            _ => None,
        }
    }

    pub fn to_numerical(&self) -> BigInt {
        let coeff_val = match &self.coeff {
            SymbolicCoefficient::Literal { value } => value.clone(),
            SymbolicCoefficient::Power { base, exponent } => {
                if let Some(exp_u32) = exponent.to_u32() {
                    base.pow(exp_u32)
                } else {
                    return BigInt::from(-999);
                }
            }
        };
        if self.poly.is_empty() {
            return coeff_val;
        }
        let mut total = BigInt::zero();
        let base_bigint = BigInt::from(self.base);
        for (exp, poly_coeff) in &self.poly {
            let term_val = if let Some(e_u32) = exp.to_u32() {
                poly_coeff * base_bigint.pow(e_u32)
            } else {
                return BigInt::from(-998);
            };
            total += term_val;
        }
        total * coeff_val
    }

    pub fn get_poly(&self) -> HashMap<String, BigInt> {
        self.poly
            .iter()
            .map(|(e, c)| (e.to_string(), c.clone()))
            .collect()
    }

    pub fn __repr__(&self) -> String {
        let coeff_part = match &self.coeff {
            SymbolicCoefficient::Literal { value } => match value.sign() {
                Sign::NoSign if self.poly.is_empty() => return "AoP(0)".to_string(),
                Sign::Plus if *value == BigInt::one() => "".to_string(),
                Sign::Minus if *value == -BigInt::one() => "-".to_string(),
                _ => format!("{} * ", value),
            },
            SymbolicCoefficient::Power { base, exponent } => format!("({}^{}) * ", base, exponent),
        };
        if self.poly.is_empty() {
            return format!("AoP({})", coeff_part.trim_end_matches(" * "));
        }
        let mut parts: Vec<_> = self.poly.iter().collect();
        parts.sort_by_key(|(e, _)| (*e).clone());
        parts.reverse();
        let poly_str = parts
            .iter()
            .map(|(e, c)| format!("@{}:{}", int_to_key_rust(e), c))
            .collect::<Vec<_>>()
            .join(", ");
        format!("AoP({}{{{}}})", coeff_part, poly_str)
    }

    pub fn power(&self, exp_val: &Self) -> PyResult<Self> {
        let n = exp_val.to_numerical();
        if n.is_zero() {
            return Ok(from_bigint(&BigInt::one(), self.base));
        }
        if n.is_one() {
            return Ok(self.clone());
        }

        let new_coeff = match &self.coeff {
            SymbolicCoefficient::Literal { value } => {
                if n < BigInt::from(10000) {
                    if let Some(n_u32) = n.to_u32() {
                        SymbolicCoefficient::Literal {
                            value: value.pow(n_u32),
                        }
                    } else {
                        SymbolicCoefficient::Power {
                            base: value.clone(),
                            exponent: n.clone(),
                        }
                    }
                } else {
                    SymbolicCoefficient::Power {
                        base: value.clone(),
                        exponent: n.clone(),
                    }
                }
            }
            SymbolicCoefficient::Power { base, exponent } => SymbolicCoefficient::Power {
                base: base.clone(),
                exponent: exponent * n.clone(),
            },
        };

        let result_poly = if self.poly.is_empty() {
            HashMap::new()
        } else {
            let n_u32 = n.to_u32().ok_or_else(|| {
                pyo3::exceptions::PyValueError::new_err(
                    "Exponent too large for polynomial expansion.",
                )
            })?;
            match expand_multinomial(&self.poly, n_u32) {
                Ok(poly) => poly,
                Err(e) => return Err(pyo3::exceptions::PyValueError::new_err(e)),
            }
        };
        Ok(Self::_new_internal(new_coeff, result_poly, self.base))
    }
}
