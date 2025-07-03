// aop_rust_core/src/internal_methods.rs

use super::aop_value::{AoPValue, SymbolicCoefficient};
use num_bigint::BigInt;
use num_traits::Zero; // <-- ADDED
use rayon::prelude::*;
use std::collections::HashMap;

impl AoPValue {
    pub fn _new_internal(
        coeff: SymbolicCoefficient,
        poly: HashMap<BigInt, BigInt>,
        base: u32,
    ) -> Self {
        let poly_filtered = poly.into_iter().filter(|(_, c)| !c.is_zero()).collect();
        Self {
            coeff,
            poly: poly_filtered,
            base,
        }
    }

    // This method is now simpler as the coefficient is handled elsewhere
    pub fn _simplify_poly(&mut self) {
        // ... (Simplification logic can be added back here if needed for the poly part)
    }

    pub fn _mul_poly_raw(
        p1: &HashMap<BigInt, BigInt>,
        p2: &HashMap<BigInt, BigInt>,
    ) -> HashMap<BigInt, BigInt> {
        if p1.is_empty() {
            return p2.clone();
        }
        if p2.is_empty() {
            return p1.clone();
        }

        p1.par_iter()
            .flat_map(|(e1, c1)| p2.par_iter().map(move |(e2, c2)| (e1 + e2, c1 * c2)))
            .fold(HashMap::new, |mut map, (exp, coeff)| {
                *map.entry(exp).or_default() += coeff;
                map
            })
            .reduce(HashMap::new, |mut map1, map2| {
                for (exp, coeff) in map2 {
                    *map1.entry(exp).or_default() += coeff;
                }
                map1
            })
    }
}
