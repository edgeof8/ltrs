import math
import cmath
from src.aopl_python_impl.aop_value import AoPValue
from src.aopl_python_impl.aop_operations import add_values, subtract_values, multiply_values, power_value, simplify_value

# Add your tests here for the aop_operations functions.
# For example:

# def test_add_values():
#     v1 = AoPValue(1, 1) # 10^1
#     v2 = AoPValue(1, 2) # 10^2
#     result = add_values(v1, v2, 10)
#     assert result.to_numerical(10) == 110

# def test_power_value_simple():
#     base_val = AoPValue(1, 1) # 10^1 (a)
#     power_val = AoPValue(1, 2) # 10^2 (b)
#     result = power_value(base_val, power_val, 10)
#     # (10^1)^(10^2) = 10^(1 * 100) = 10^100
#     assert result.coeff == 1.0
#     assert result.exponent == 100

# def test_power_value_recursive_exponent():
#     # This test case would be for a^(b^c) where b^c is a recursive AoPValue
#     # Given the new parser, this structure should be created.
#     # Example: a^j^b -> a^(j^b)
#     # j^b would be AoPValue(1.0, AoPValue(1.0, 1000))
#     # This test needs to be carefully constructed to reflect the new right-associativity.
#     pass
