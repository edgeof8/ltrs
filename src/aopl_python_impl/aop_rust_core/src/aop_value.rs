// aop_rust_core/src/aop_value.rs

use num_bigint::BigInt;
use pyo3::prelude::*;
use std::collections::HashMap;

// CORRECT: This is a pure Rust enum, not a Python class.
#[derive(Debug, Clone, PartialEq)]
pub enum SymbolicCoefficient {
    Literal { value: BigInt },
    Power { base: BigInt, exponent: BigInt },
}

#[pymethods]
impl SymbolicCoefficient {
    // This function will be called by Python's pickle.
    fn __reduce__(&self) -> PyResult<(PyObject, (PyObject,))> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let constructor = self.py_class(py).to_object(py);

        let args = match self {
            SymbolicCoefficient::Literal { value } => {
                // Tag 1 for Literal, followed by its data
                (1i32, value.clone()).to_object(py)
            }
            SymbolicCoefficient::Power { base, exponent } => {
                // Tag 2 for Power, followed by its data
                (2i32, base.clone(), exponent.clone()).to_object(py)
            }
        };

        Ok((constructor, (args,)))
    }

    // We also need a constructor that can be called by pickle's __setstate__
    // or a similar mechanism. The simplest is a static method.
    #[staticmethod]
    fn __reconstruct__(args: PyObject) -> PyResult<Self> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        // Try to extract as a Literal tuple: (1, value)
        if let Ok((tag, value)) = args.extract::<(i32, BigInt)>(py) {
            if tag == 1 {
                return Ok(SymbolicCoefficient::Literal { value });
            }
        }

        // Try to extract as a Power tuple: (2, base, exponent)
        if let Ok((tag, base, exponent)) = args.extract::<(i32, BigInt, BigInt)>(py) {
            if tag == 2 {
                return Ok(SymbolicCoefficient::Power { base, exponent });
            }
        }

        Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid state for SymbolicCoefficient reconstruction",
        ))
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct AoPValue {
    // This field is NOT directly settable from Python, only gettable via methods.
    pub coeff: SymbolicCoefficient,
    pub poly: HashMap<BigInt, BigInt>,
    #[pyo3(get, set)]
    pub base: u32,
}
