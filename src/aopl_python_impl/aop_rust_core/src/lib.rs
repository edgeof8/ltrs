// aop_rust_core/src/lib.rs

#![allow(non_local_definitions)]

// Declare the modules that make up our library
mod aop_value;
mod exponent_map;
mod internal_methods;
mod multinomial;
mod operators;
mod python_interface;

// Import the main struct to make it available to the pymodule
use aop_value::AoPValue;
use pyo3::prelude::*;

// Define the python module
#[pymodule]
fn aop_rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<AoPValue>()?;
    // DO NOT add SymbolicCoefficient here.
    Ok(())
}
