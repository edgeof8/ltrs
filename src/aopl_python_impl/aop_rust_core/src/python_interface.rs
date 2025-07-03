// aop_rust_core/src/python_interface.rs

use super::aop_value::{AoPValue, CoeffData, SymbolicCoefficientPy};
use super::exponent_map::int_to_key_rust;
use super::multinomial::expand_multinomial;
use num_bigint::{BigInt, Sign};
use num_integer::Integer;
use num_traits::{One, Signed, ToPrimitive, Zero}; // Added Zero back
use pyo3::prelude::*;
use std::collections::HashMap;

// --- NEW: Manual ToPyObject implementation ---
// This tells PyO3 how to convert our Rust struct into a Python object.
impl ToPyObject for SymbolicCoefficientPy {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        // Create a new Python instance of the SymbolicCoefficientPy class
        // and pass `self` (the Rust struct) to its constructor.
        Py::new(py, self.clone()).unwrap().to_object(py)
    }
}

#[pymethods]
impl SymbolicCoefficientPy {
    #[new]
    fn __new__() -> Self {
        SymbolicCoefficientPy {
            data: CoeffData::Literal(BigInt::zero()),
        }
    }

    // Correct: Get Python instance from the method signature
    fn __getstate__<'py>(&self, py: Python<'py>) -> PyResult<PyObject> {
        match &self.data {
            CoeffData::Literal(val) => Ok((1, val).to_object(py)),
            CoeffData::Power { base, exponent } => Ok((2, base, exponent).to_object(py)),
        }
    }

    // Correct: Get Python instance from the method signature
    fn __setstate__(&mut self, state: PyObject, py: Python) -> PyResult<()> {
        if let Ok((tag, value)) = state.extract::<(i32, BigInt)>(py) {
            if tag == 1 {
                self.data = CoeffData::Literal(value);
                return Ok(());
            }
        }
        if let Ok((tag, base, exponent)) = state.extract::<(i32, BigInt, BigInt)>(py) {
            if tag == 2 {
                self.data = CoeffData::Power { base, exponent };
                return Ok(());
            }
        }
        Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid state for SymbolicCoefficient",
        ))
    }
}

fn from_bigint(n: &BigInt, base: u32) -> AoPValue {
    let coeff_data = CoeffData::Literal(if n.is_negative() {
        -BigInt::one()
    } else {
        BigInt::one()
    });
    let coeff = SymbolicCoefficientPy { data: coeff_data };
    let mut n_abs = n.abs();
    let base_bigint = BigInt::from(base);
    let mut poly = HashMap::new();
    let mut exp = BigInt::zero(); // Correct: uses the Zero trait
    while n_abs > BigInt::from(0) {
        let (new_n, remainder) = n_abs.div_mod_floor(&base_bigint);
        if remainder != BigInt::from(0) {
            poly.insert(exp.clone(), remainder);
        }
        n_abs = new_n;
        exp += 1;
    }
    AoPValue::_new_internal(coeff, poly, base)
}

#[pymethods]
impl AoPValue {
    // --- CORRECTED: A SINGLE, UNIFIED CONSTRUCTOR ---
    #[new]
    fn __new__(
        poly_str_keys: Option<HashMap<String, BigInt>>,
        base: Option<u32>,
        coeff: Option<BigInt>,
    ) -> Self {
        let final_base = base.unwrap_or(10);
        let coeff_data = CoeffData::Literal(coeff.unwrap_or_else(BigInt::one));
        let final_coeff = SymbolicCoefficientPy { data: coeff_data };
        let poly = poly_str_keys
            .unwrap_or_default()
            .into_iter()
            .filter_map(|(k, v)| k.parse::<BigInt>().ok().map(|exp| (exp, v)))
            .collect();
        Self::_new_internal(final_coeff, poly, final_base)
    }

    // --- Pickle Protocol Implementation ---

    // 1. __getnewargs__: Tells pickle what to pass to __new__ when unpickling.
    //    We want it to create a default object, so we return an empty tuple.
    fn __getnewargs__(&self) -> PyResult<(Option<()>, Option<()>, Option<()>)> {
        Ok((None, None, None))
    }

    #[staticmethod]
    pub fn from_literal(literal_str: &str, base: u32) -> PyResult<Self> {
        // This regex logic is moved from Python to Rust
        let term_pattern = regex::Regex::new(r"(\d+)?([a-zA-Z])|(\d+)").unwrap();
        let mut matches = Vec::new();
        for cap in term_pattern.find_iter(literal_str) {
            matches.push(term_pattern.captures(cap.as_str()).unwrap());
        }

        let mut poly = HashMap::new();
        let mut main_coeff = BigInt::one();

        if matches.len() == 1 {
            let cap = &matches[0];
            if let Some(letter_match) = cap.get(2) {
                let letter = letter_match.as_str().chars().next().unwrap();
                let coeff_str = cap.get(1).map_or("1", |m| m.as_str());
                main_coeff = coeff_str.parse().unwrap();
                let exp = super::exponent_map::LETTER_TO_EXPONENT_MAP
                    .get(&letter)
                    .unwrap()
                    .clone();
                poly.insert(exp, BigInt::one());

                let coeff_data = CoeffData::Literal(main_coeff);
                let final_coeff = SymbolicCoefficientPy { data: coeff_data };
                return Ok(Self::_new_internal(final_coeff, poly, base));
            }
        }

        // Fallback for multi-term
        for cap in matches {
            if let Some(letter_match) = cap.get(2) {
                let letter = letter_match.as_str().chars().next().unwrap();
                let coeff_str = cap.get(1).map_or("1", |m| m.as_str());
                let coeff_val: BigInt = coeff_str.parse().unwrap();
                let exp = super::exponent_map::LETTER_TO_EXPONENT_MAP
                    .get(&letter)
                    .unwrap()
                    .clone();
                *poly.entry(exp).or_default() += coeff_val;
            } else if let Some(num_match) = cap.get(3) {
                let num_val: BigInt = num_match.as_str().parse().unwrap();
                *poly.entry(BigInt::zero()).or_default() += num_val;
            }
        }

        let coeff_data = CoeffData::Literal(main_coeff);
        let final_coeff = SymbolicCoefficientPy { data: coeff_data };
        Ok(Self::_new_internal(final_coeff, poly, base))
    }

    #[staticmethod]
    pub fn from_number(n: &PyAny, base: u32) -> PyResult<Self> {
        let n_bigint: BigInt = n.extract()?;
        Ok(from_bigint(&n_bigint, base))
    }

    pub fn to_numerical(&self) -> BigInt {
        let coeff_val = match &self.coeff.data {
            CoeffData::Literal(value) => value.clone(),
            CoeffData::Power { base, exponent } => {
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
        let mut total = BigInt::from(0);
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
        let coeff_part = match &self.coeff.data {
            CoeffData::Literal(value) => match value.sign() {
                Sign::NoSign if self.poly.is_empty() => return "AoP(0)".to_string(),
                Sign::Plus if *value == BigInt::one() => "".to_string(),
                Sign::Minus if *value == -BigInt::one() => "-".to_string(),
                _ => format!("{} * ", value),
            },
            CoeffData::Power { base, exponent } => format!("({}^{}) * ", base, exponent),
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
        if n == BigInt::from(0) {
            return Ok(from_bigint(&BigInt::one(), self.base));
        }
        if n == BigInt::one() {
            return Ok(self.clone());
        }

        let new_coeff_data = match &self.coeff.data {
            CoeffData::Literal(value) => {
                if n < BigInt::from(10000) {
                    if let Some(n_u32) = n.to_u32() {
                        CoeffData::Literal(value.pow(n_u32))
                    } else {
                        CoeffData::Power {
                            base: value.clone(),
                            exponent: n.clone(),
                        }
                    }
                } else {
                    CoeffData::Power {
                        base: value.clone(),
                        exponent: n.clone(),
                    }
                }
            }
            CoeffData::Power { base, exponent } => CoeffData::Power {
                base: base.clone(),
                exponent: exponent * n.clone(),
            },
        };
        let new_coeff = SymbolicCoefficientPy {
            data: new_coeff_data,
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

    #[getter]
    pub fn get_coeff_as_power(&self) -> Option<(BigInt, BigInt)> {
        match &self.coeff.data {
            CoeffData::Power { base, exponent } => Some((base.clone(), exponent.clone())),
            _ => None,
        }
    }

    fn __getstate__<'py>(&self, py: Python<'py>) -> PyResult<PyObject> {
        Ok((self.coeff.clone(), self.poly.clone(), self.base).to_object(py))
    }

    fn __setstate__(&mut self, state: PyObject, py: Python) -> PyResult<()> {
        let (coeff, poly, base): (SymbolicCoefficientPy, HashMap<BigInt, BigInt>, u32) =
            state.extract(py)?;
        self.coeff = coeff;
        self.poly = poly;
        self.base = base;
        Ok(())
    }
}
