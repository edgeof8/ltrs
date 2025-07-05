// aop_rust_core/src/aop_value.rs

use num_bigint::BigInt;
use pyo3::prelude::*;
use std::collections::HashMap;

#[pyclass]
#[derive(Debug, Clone)]
pub struct AoPValue {
    #[pyo3(get, set)]
    pub coeff: BigInt,
    #[pyo3(set)] // The getter is manual, so we only need the setter here.
    pub poly: HashMap<BigInt, BigInt>,
    #[pyo3(get, set)]
    pub base: u32,
}
