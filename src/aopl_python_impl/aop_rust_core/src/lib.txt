// aop_rust_core/src/lib.rs

#![allow(non_local_definitions)]

mod aop_value;
mod exponent_map;
mod internal_methods;
mod multinomial;
mod operators;
mod python_interface;

use aop_value::AoPValue;
use pyo3::prelude::*;

#[pymodule]
fn aop_rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<AoPValue>()?;
    Ok(())
}
