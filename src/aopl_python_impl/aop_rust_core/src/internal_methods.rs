// aop_rust_core/src/internal_methods.rs

use super::aop_value::AoPValue;
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use rayon::prelude::*;
use std::collections::HashMap;

impl AoPValue {
    pub fn _new_internal(coeff: BigInt, poly: HashMap<BigInt, BigInt>, base: u32) -> Self {
        let poly_filtered = poly.into_iter().filter(|(_, c)| !c.is_zero()).collect();
        Self {
            coeff,
            poly: poly_filtered,
            base,
        }
    }

    pub fn _simplify(&mut self) {
        if self.poly.is_empty() {
            return;
        }
        self._handle_neg_coeffs();
        let base_bigint = BigInt::from(self.base);
        let mut sorted_exps: Vec<_> = self.poly.keys().cloned().collect();
        sorted_exps.sort_unstable();
        let mut i = 0;
        while i < sorted_exps.len() {
            let exp = sorted_exps[i].clone();
            if let Some(coeff) = self.poly.get_mut(&exp) {
                if coeff.abs() >= base_bigint {
                    let (new_carry, remainder) = coeff.clone().div_mod_floor(&base_bigint);
                    *coeff = remainder;
                    if !new_carry.is_zero() {
                        let next_exp = exp.clone() + BigInt::one();
                        let entry = self.poly.entry(next_exp.clone()).or_default();
                        *entry += new_carry;
                        if let Err(pos) = sorted_exps.binary_search(&next_exp) {
                            sorted_exps.insert(pos, next_exp);
                        }
                    }
                }
            }
            i += 1;
        }
        self.poly.retain(|_, v| !v.is_zero());
    }

    pub fn _handle_neg_coeffs(&mut self) {
        if self.poly.values().all(|c| !c.is_negative()) {
            return;
        }
        let mut sorted_exps: Vec<_> = self.poly.keys().cloned().collect();
        sorted_exps.sort_unstable();
        let base_bigint = BigInt::from(self.base);
        let one = BigInt::one();
        for exp in sorted_exps {
            if let Some(coeff_val) = self.poly.get(&exp).filter(|c| c.is_negative()) {
                let coeff_val = coeff_val.clone();
                let borrows_needed = (coeff_val.abs() + &base_bigint - &one) / &base_bigint;
                *self.poly.entry(exp.clone()).or_default() += &borrows_needed * &base_bigint;
                *self.poly.entry(exp.clone() + &one).or_default() -= borrows_needed;
            }
        }
        self.poly.retain(|_, v| !v.is_zero());
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

    /// Flatten `coeff * poly` into a single exponent map in Z[X], X = base.
    /// A coefficient-only value (empty poly) becomes the constant term c X^0.
    pub fn as_distributed_poly(&self) -> HashMap<BigInt, BigInt> {
        let mut new_poly = HashMap::new();
        if self.poly.is_empty() {
            if !self.coeff.is_zero() {
                new_poly.insert(BigInt::zero(), self.coeff.clone());
            }
            return new_poly;
        }
        for (exp, p_coeff) in &self.poly {
            let c = &self.coeff * p_coeff;
            if !c.is_zero() {
                *new_poly.entry(exp.clone()).or_default() += c;
            }
        }
        new_poly.retain(|_, c| !c.is_zero());
        new_poly
    }

    /// Build an AoPValue from a distributed polynomial and carry.
    /// The empty polynomial is the integer 0, not the constant 1.
    pub fn from_distributed_poly(poly: HashMap<BigInt, BigInt>, base: u32) -> Self {
        let poly: HashMap<BigInt, BigInt> = poly
            .into_iter()
            .filter(|(_, c)| !c.is_zero())
            .collect();
        if poly.is_empty() {
            return Self::_new_internal(BigInt::zero(), HashMap::new(), base);
        }
        let mut result = Self::_new_internal(BigInt::one(), poly, base);
        result._simplify();
        if result.poly.is_empty() {
            return Self::_new_internal(BigInt::zero(), HashMap::new(), base);
        }
        result
    }

    /// Unique non-negative digit map after distributing the leading coefficient
    /// and carrying. Empty means zero. Does not expand into a single integer.
    pub fn canonical_poly(&self) -> HashMap<BigInt, BigInt> {
        Self::from_distributed_poly(self.as_distributed_poly(), self.base).poly
    }

    /// True iff both values have the same base and the same canonical digit map.
    /// Factored `1024 * X^20` and carried `X^23 + 2 X^21 + 4 X^20` compare equal.
    pub fn canonical_eq(&self, other: &Self) -> bool {
        self.base == other.base && self.canonical_poly() == other.canonical_poly()
    }

    pub fn poly_div_exact(
        dividend: &HashMap<BigInt, BigInt>,
        divisor: &HashMap<BigInt, BigInt>,
    ) -> Result<HashMap<BigInt, BigInt>, PolyDivError> {
        if is_zero_poly(divisor) {
            return Err(PolyDivError::DivisionByZero);
        }
        if is_zero_poly(dividend) {
            return Ok(HashMap::new());
        }

        let (div_exp, div_coeff) = leading_term(divisor).expect("non-zero divisor has a leading term");
        let mut remainder = dividend.clone();
        remainder.retain(|_, c| !c.is_zero());
        let mut quotient: HashMap<BigInt, BigInt> = HashMap::new();

        while let Some((rem_exp, rem_coeff)) = leading_term(&remainder) {
            if rem_exp < div_exp {
                break;
            }
            if !rem_coeff.is_multiple_of(&div_coeff) {
                return Err(PolyDivError::DoesNotDivide);
            }
            let q_coeff = &rem_coeff / &div_coeff;
            if q_coeff.is_zero() {
                return Err(PolyDivError::DoesNotDivide);
            }
            let q_exp = rem_exp - &div_exp;
            for (e, c) in divisor {
                if c.is_zero() {
                    continue;
                }
                let exp = e + &q_exp;
                *remainder.entry(exp).or_default() -= c * &q_coeff;
            }
            remainder.retain(|_, c| !c.is_zero());
            *quotient.entry(q_exp).or_default() += q_coeff;
        }

        if !is_zero_poly(&remainder) {
            return Err(PolyDivError::DoesNotDivide);
        }
        quotient.retain(|_, c| !c.is_zero());
        Ok(quotient)
    }

    pub fn divide_poly(&self, other: &Self) -> Result<Self, PolyDivError> {
        if self.base != other.base {
            return Err(PolyDivError::DifferentBases);
        }
        let dividend = self.as_distributed_poly();
        let divisor = other.as_distributed_poly();
        match Self::poly_div_exact(&dividend, &divisor) {
            Ok(quotient) => Ok(Self::from_quotient_poly(quotient, self.base)),
            Err(PolyDivError::DoesNotDivide) => self.divide_exact_integer(other),
            Err(err) => Err(err),
        }
    }

    fn from_quotient_poly(quotient: HashMap<BigInt, BigInt>, base: u32) -> Self {
        if quotient.is_empty() {
            return AoPValue::_new_internal(BigInt::zero(), HashMap::new(), base);
        }
        let mut result = AoPValue::_new_internal(BigInt::one(), quotient, base);
        result._simplify();
        result
    }

    /// `_simplify` rewrites 10 as X^1, so formal Z[X] division of 10/2 is X/2
    /// and fails even though the number 10 is divisible by 2. Fall back to
    /// exact integer division and re-encode the quotient as an AoP polynomial.
    fn divide_exact_integer(&self, other: &Self) -> Result<Self, PolyDivError> {
        let dividend = self
            .try_to_numerical()
            .map_err(|_| PolyDivError::ExponentTooLarge)?;
        let divisor = other
            .try_to_numerical()
            .map_err(|_| PolyDivError::ExponentTooLarge)?;
        if divisor.is_zero() {
            return Err(PolyDivError::DivisionByZero);
        }
        if !dividend.is_multiple_of(&divisor) {
            return Err(PolyDivError::DoesNotDivide);
        }
        Ok(AoPValue::from_numerical_internal(
            dividend / divisor,
            self.base,
        ))
    }

    /// Integer gcd of the two values, without expanding `B^k` when the units
    /// parts fit in `u32` exponents. Writes `n = B^{v(n)} · u(n)` and returns
    /// `B^{min(v)} · gcd(B^{|v1-v2|} u_hi, u_lo)`, computing the remaining gcd
    /// via `B^e mod |u_lo|` so shared factors of the base are kept.
    /// `gcd(0, n) = |n|`.
    pub fn integer_gcd(&self, other: &Self) -> Result<Self, PolyDivError> {
        if self.base != other.base {
            return Err(PolyDivError::DifferentBases);
        }
        let a = self.as_distributed_poly();
        let b = other.as_distributed_poly();
        if is_zero_poly(&a) {
            return Ok(Self::from_distributed_poly(abs_poly(&b), self.base));
        }
        if is_zero_poly(&b) {
            return Ok(Self::from_distributed_poly(abs_poly(&a), self.base));
        }
        let (v1, u1) = strip_valuation(&a);
        let (v2, u2) = strip_valuation(&b);
        let v = if v1 < v2 { v1.clone() } else { v2.clone() };
        let e1 = &v1 - &v;
        let e2 = &v2 - &v;
        let g_units = gcd_after_valuation(&u1, &e1, &u2, &e2, self.base)?;
        Ok(mul_by_base_power(g_units, v, self.base))
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PolyDivError {
    DivisionByZero,
    DoesNotDivide,
    DifferentBases,
    ExponentTooLarge,
}

fn is_zero_poly(p: &HashMap<BigInt, BigInt>) -> bool {
    p.is_empty() || p.values().all(|c| c.is_zero())
}

fn leading_term(p: &HashMap<BigInt, BigInt>) -> Option<(BigInt, BigInt)> {
    p.iter()
        .filter(|(_, c)| !c.is_zero())
        .max_by(|a, b| a.0.cmp(b.0))
        .map(|(e, c)| (e.clone(), c.clone()))
}

fn abs_poly(p: &HashMap<BigInt, BigInt>) -> HashMap<BigInt, BigInt> {
    p.iter()
        .filter(|(_, c)| !c.is_zero())
        .map(|(e, c)| (e.clone(), c.abs()))
        .collect()
}

fn strip_valuation(p: &HashMap<BigInt, BigInt>) -> (BigInt, HashMap<BigInt, BigInt>) {
    let v = p
        .iter()
        .filter(|(_, c)| !c.is_zero())
        .map(|(e, _)| e)
        .min()
        .cloned()
        .unwrap_or_else(BigInt::zero);
    let units = p
        .iter()
        .filter(|(_, c)| !c.is_zero())
        .map(|(e, c)| (e - &v, c.clone()))
        .collect();
    (v, units)
}

fn poly_abs_int(p: &HashMap<BigInt, BigInt>, base: u32) -> Result<BigInt, BigInt> {
    AoPValue::from_distributed_poly(p.clone(), base)
        .try_to_numerical()
        .map(|n| n.abs())
}

/// gcd(B^{e1} u1, B^{e2} u2) with at least one of e1, e2 zero after stripping
/// the shared valuation.
fn gcd_after_valuation(
    u1: &HashMap<BigInt, BigInt>,
    e1: &BigInt,
    u2: &HashMap<BigInt, BigInt>,
    e2: &BigInt,
    base: u32,
) -> Result<BigInt, PolyDivError> {
    let n1 = poly_abs_int(u1, base);
    let n2 = poly_abs_int(u2, base);
    match (n1, n2) {
        (Ok(a), Ok(b)) if e1.is_zero() && e2.is_zero() => Ok(a.gcd(&b)),
        (Ok(a), Ok(b)) if e2.is_zero() => Ok(gcd_base_power_times(base, e1, &a, &b)),
        (Ok(a), Ok(b)) if e1.is_zero() => Ok(gcd_base_power_times(base, e2, &b, &a)),
        (Ok(a), Err(_)) if a.is_one() && e2.is_zero() => Ok(BigInt::one()),
        (Err(_), Ok(b)) if b.is_one() && e1.is_zero() => Ok(BigInt::one()),
        _ => Err(PolyDivError::ExponentTooLarge),
    }
}

/// gcd(base^exp * units, other) via modular exponentiation. Does not expand
/// `base^exp` when `exp` is huge.
fn gcd_base_power_times(base: u32, exp: &BigInt, units: &BigInt, other: &BigInt) -> BigInt {
    let w = other.abs();
    if w.is_zero() {
        return units.abs();
    }
    if w.is_one() {
        return BigInt::one();
    }
    let bmod = BigInt::from(base).modpow(exp, &w);
    let umod = units.abs() % &w;
    (&bmod * umod % &w).gcd(&w)
}

fn mul_by_base_power(g: BigInt, v: BigInt, base: u32) -> AoPValue {
    let val = AoPValue::from_numerical_internal(g.abs(), base);
    if v.is_zero() {
        return val;
    }
    let monomial = AoPValue::_new_internal(
        BigInt::one(),
        HashMap::from([(v, BigInt::one())]),
        base,
    );
    &val * &monomial
}

#[cfg(test)]
mod tests {
    use super::*;

    fn from_n(n: i64, base: u32) -> AoPValue {
        AoPValue::from_numerical_internal(BigInt::from(n), base)
    }

    fn monomial(exp: i64, base: u32) -> AoPValue {
        AoPValue::_new_internal(
            BigInt::one(),
            HashMap::from([(BigInt::from(exp), BigInt::one())]),
            base,
        )
    }

    #[test]
    fn gcd_small_integers() {
        let g = from_n(48, 10).integer_gcd(&from_n(18, 10)).unwrap();
        assert_eq!(g.try_to_numerical().unwrap(), BigInt::from(6));
        let z = from_n(0, 10).integer_gcd(&from_n(18, 10)).unwrap();
        assert_eq!(z.try_to_numerical().unwrap(), BigInt::from(18));
    }

    #[test]
    fn gcd_powers_of_the_base() {
        let c = monomial(3, 10);
        let a = monomial(1, 10);
        let g = c.integer_gcd(&a).unwrap();
        assert_eq!(g.canonical_poly(), a.canonical_poly());
    }

    #[test]
    fn gcd_huge_monomial_with_small_int() {
        let huge = monomial(1 << 40, 10);
        let twenty_five = from_n(25, 10);
        let g = huge.integer_gcd(&twenty_five).unwrap();
        assert_eq!(g.try_to_numerical().unwrap(), BigInt::from(25));
    }

    #[test]
    fn gcd_common_power_of_the_base() {
        let k: i64 = 1 << 40;
        let left = monomial(k, 10);
        let right = monomial(k - 1, 10);
        let g = left.integer_gcd(&right).unwrap();
        assert_eq!(
            g.poly,
            HashMap::from([(BigInt::from(k - 1), BigInt::one())])
        );
    }

    #[test]
    fn divide_monomials() {
        let c = monomial(3, 10);
        let a = monomial(1, 10);
        let q = c.divide_poly(&a).unwrap();
        assert_eq!(
            q.canonical_poly(),
            HashMap::from([(BigInt::from(2), BigInt::one())])
        );
    }

    #[test]
    fn canonical_eq_factored_and_carried() {
        let factored = AoPValue::_new_internal(
            BigInt::from(1024),
            HashMap::from([(BigInt::from(20), BigInt::one())]),
            10,
        );
        let t = monomial(20, 10);
        let carried = &from_n(1024, 10) * &t;
        assert!(factored.canonical_eq(&carried));
        assert_eq!(
            factored.canonical_poly(),
            HashMap::from([
                (BigInt::from(20), BigInt::from(4)),
                (BigInt::from(21), BigInt::from(2)),
                (BigInt::from(23), BigInt::one()),
            ])
        );
    }

    #[test]
    fn mixed_bases_gcd_errors() {
        let left = from_n(10, 10);
        let right = from_n(10, 2);
        assert_eq!(
            left.integer_gcd(&right).unwrap_err(),
            PolyDivError::DifferentBases
        );
    }
}
