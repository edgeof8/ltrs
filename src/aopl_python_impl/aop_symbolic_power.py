# aopl_python_impl/aop_symbolic_power.py
from __future__ import annotations
from typing import Dict, Union
from .aop_value import AoPValue, int_to_key, key_to_int
from .aop_logger import log_pow

class SymbolicPower:
    def __init__(self, base: 'AoPValue', exponent: 'AoPValue | SymbolicPower'):
        self.base = base
        self.exponent = exponent

    def __repr__(self) -> str:
        return f"SymbolicPower({self.base!r} ^ {self.exponent!r})"

    def to_numerical(self) -> int:
        # Intelligent Dispatcher for evaluation
        if self.base.is_pure_power() and (isinstance(self.exponent, AoPValue) and self.exponent.is_pure_power()):
            # Use logarithmic shortcut for pure powers
            log_pow(f"SymbolicPower: Using logarithmic shortcut for {self!r}")
            k_str = list(self.base.poly.keys())[0]
            k = key_to_int(k_str, self.base.base)
            n_str = list(self.exponent.poly.keys())[0]
            n = key_to_int(n_str, self.base.base)
            new_exp = k * (self.base.base ** n)
            return self.base.base ** new_exp
        elif isinstance(self.exponent, AoPValue) and self.exponent.is_small_integer():
            # Handle binomial expansion or simple exponentiation if exponent is small
            log_pow(f"SymbolicPower: Using exponentiation for small exponent in {self!r}")
            exp_val = self.exponent.to_numerical()
            if exp_val < 10:  # Arbitrary threshold for small exponent
                result = AoPValue({int_to_key(0, self.base.base): 1}, self.base.base)
                current_base = self.base
                while exp_val > 0:
                    if exp_val % 2 == 1:
                        result *= current_base
                    current_base *= current_base
                    exp_val //= 2
                return result.to_numerical()
            else:
                raise OverflowError(f"Exponent too large for direct computation: {self.exponent!r}")
        else:
            # Fallback to slow exponentiation if necessary
            log_pow(f"SymbolicPower: Fallback to slow exponentiation for {self!r}")
            if isinstance(self.exponent, SymbolicPower):
                exp_val = self.exponent.to_numerical()
            else:
                exp_val = self.exponent.to_numerical()
            result = AoPValue({int_to_key(0, self.base.base): 1}, self.base.base)
            current_base = self.base
            while exp_val > 0:
                if exp_val % 2 == 1:
                    result *= current_base
                current_base *= current_base
                exp_val //= 2
            return result.to_numerical()

    def is_pure_power(self) -> bool:
        return self.base.is_pure_power()

    def is_small_integer(self) -> bool:
        if isinstance(self.exponent, SymbolicPower):
            return False
        return self.exponent.is_small_integer()

    def __add__(self, other: 'AoPValue | SymbolicPower') -> 'AoPValue':
        # Convert to numerical or AoPValue for addition
        if isinstance(other, SymbolicPower):
            return AoPValue.from_number(self.to_numerical() + other.to_numerical(), self.base.base)
        return AoPValue.from_number(self.to_numerical() + other.to_numerical(), self.base.base)

    def __sub__(self, other: 'AoPValue | SymbolicPower') -> 'AoPValue':
        # Convert to numerical or AoPValue for subtraction
        if isinstance(other, SymbolicPower):
            return AoPValue.from_number(self.to_numerical() - other.to_numerical(), self.base.base)
        return AoPValue.from_number(self.to_numerical() - other.to_numerical(), self.base.base)

    def __mul__(self, other: 'AoPValue | SymbolicPower') -> 'SymbolicPower | AoPValue':
        # Apply exponent rules if possible
        if isinstance(other, SymbolicPower) and self.base == other.base:
            # (a^b) * (a^c) = a^(b+c)
            if isinstance(self.exponent, AoPValue) and isinstance(other.exponent, AoPValue):
                new_exp = self.exponent + other.exponent
                return SymbolicPower(self.base, new_exp)
            else:
                return AoPValue.from_number(self.to_numerical() * other.to_numerical(), self.base.base)
        elif isinstance(other, AoPValue) and other.is_pure_power() and self.base == other:
            # (a^b) * a^c = a^(b+c)
            if isinstance(self.exponent, AoPValue):
                new_exp = self.exponent + other
                return SymbolicPower(self.base, new_exp)
            else:
                return AoPValue.from_number(self.to_numerical() * other.to_numerical(), self.base.base)
        return AoPValue.from_number(self.to_numerical() * other.to_numerical(), self.base.base)

    def __pow__(self, other: 'AoPValue | SymbolicPower') -> 'SymbolicPower':
        # (a^b)^c = a^(b*c)
        if isinstance(self.exponent, AoPValue) and isinstance(other, AoPValue):
            new_exp = self.exponent * other
            return SymbolicPower(self.base, new_exp)
        elif isinstance(other, SymbolicPower):
            return SymbolicPower(self.base, other)
        else:
            return SymbolicPower(self.base, other)
