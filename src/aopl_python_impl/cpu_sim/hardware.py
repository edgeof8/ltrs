# aopl_python_impl/cpu_sim/hardware.py

from typing import List, Tuple, Callable
import random # Added import for the __main__ block

# These functions remain module-level as they are utility/primitive operations
# used by the CPU methods and potentially elsewhere.

# --- Representation and Conversion ---

def number_to_bitlist(n: int) -> List[int]:
    """Converts an integer to its bit-list representation (LSB first)."""
    if n == 0: return [0]
    bits = []
    while n > 0:
        bits.append(n & 1)
        n >>= 1
    return bits

def bitlist_to_number(bits: List[int]) -> int:
    """Converts a bit-list back to an integer."""
    n = 0
    for i, bit in enumerate(bits):
        if bit == 1:
            n += (1 << i)
    return n

# --- Simulated "Hardware" Primitives (Module-level helpers) ---

def _add_primitive(b1: List[int], b2: List[int]) -> List[int]: # Renamed to avoid conflict if CPU had an _add method
    """General-purpose adder. Returns a *new* bitlist (does not modify inputs)."""
    result = []
    carry = 0
    i = 0
    max_len = max(len(b1), len(b2))
    b1_copy = b1[:]
    b2_copy = b2[:]
    while i < max_len or carry:
        val1 = b1_copy[i] if i < len(b1_copy) else 0
        val2 = b2_copy[i] if i < len(b2_copy) else 0
        s = val1 + val2 + carry
        result.append(s % 2)
        carry = s // 2
        i += 1
    return result

def _subtract_primitive(b1: List[int], b2: List[int]) -> List[int]: # Renamed
    """Helper for Karatsuba. Assumes b1 >= b2. Returns a *new* bitlist."""
    result = []
    borrow = 0
    i = 0
    max_len = max(len(b1), len(b2))
    b1_copy = b1[:]
    b2_copy = b2[:]
    while i < max_len:
        val1 = b1_copy[i] if i < len(b1_copy) else 0
        val2 = b2_copy[i] if i < len(b2_copy) else 0
        s = val1 - val2 - borrow
        if s < 0:
            s += 2
            borrow = 1
        else:
            borrow = 0
        result.append(s)
        i += 1
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result

def _shift_primitive(bits: List[int], amount: int) -> List[int]: # Renamed
    if not any(bits): return [0]
    return [0] * amount + bits

def _add_sparse_inplace_primitive(bits: List[int], exp: int) -> None: # Renamed
    """Adds 2^exp to bits, modifying 'bits' in-place."""
    i = exp
    while True:
        if i >= len(bits):
            bits.extend([0] * (i - len(bits) + 1))
        if bits[i] == 1:
            bits[i] = 0
            i += 1
        else:
            bits[i] = 1
            return

class CPU:
    def __init__(self):
        # Constants for decision logic, can be tuned
        self.KARATSUBA_THRESHOLD_BITS = 1024
        self.DENSE_THRESHOLD_FACTOR = 0.9 # e.g., 90% of bits are set
        self.SPARSE_POPCOUNT_THRESHOLD = 2

        self.LUT_CHUNK_SIZE = 8 # For 8-bit chunks
        self.lookup_table: dict[tuple[int, int], int] = {}
        self._precompute_lookup_table()

    def _precompute_lookup_table(self):
        """Precomputes products for small numbers to populate the lookup table."""
        limit = 1 << self.LUT_CHUNK_SIZE
        for i in range(limit):
            for j in range(limit):
                self.lookup_table[(i, j)] = i * j

    def _get_chunks(self, n: int, chunk_size: int) -> List[int]:
        """Helper to break a number into chunks of chunk_size bits."""
        if n == 0: return [0]
        chunks = []
        mask = (1 << chunk_size) - 1
        while n > 0:
            chunks.append(n & mask)
            n >>= chunk_size
        return chunks if chunks else [0]

    def _multiply_lookup_table(self, n1: int, n2: int) -> int:
        """Algorithm 4: Lookup Table based multiplication."""
        if n1 == 0 or n2 == 0: return 0

        # Ensure numbers are positive for chunking logic, handle sign at the end if needed
        # For this simulation, assuming positive inputs as other methods do.

        n1_chunks = self._get_chunks(n1, self.LUT_CHUNK_SIZE)
        n2_chunks = self._get_chunks(n2, self.LUT_CHUNK_SIZE)

        total_result_bits = [0] # Initialize as bitlist for _add_primitive

        for i, c_i in enumerate(n1_chunks):
            for j, d_j in enumerate(n2_chunks):
                partial_product_val = self.lookup_table.get((c_i, d_j), 0) # Should always be found

                if partial_product_val == 0:
                    continue

                shift_amount = (i + j) * self.LUT_CHUNK_SIZE

                # Convert shifted partial product to bitlist to use _add_primitive
                # This is the "fair" way to do it in the simulation context
                term_to_add_val = partial_product_val << shift_amount
                term_to_add_bits = number_to_bitlist(term_to_add_val)

                total_result_bits = _add_primitive(total_result_bits, term_to_add_bits)

        return bitlist_to_number(total_result_bits)

    def _multiply_schoolbook(self, n1: int, n2: int) -> int:
        """Algorithm 1: Standard iterative schoolbook method."""
        if n1 == 0 or n2 == 0: return 0
        b1 = number_to_bitlist(n1)
        b2 = number_to_bitlist(n2)
        total = [0]
        for i, bit_n2 in enumerate(b2):
            if bit_n2 == 1:
                term_to_add = _shift_primitive(b1, i)
                total = _add_primitive(total, term_to_add)
        return bitlist_to_number(total)

    def _multiply_aop_optimized(self, n1: int, n2: int) -> int:
        """Algorithm 2: The AoP/cross-product method (Optimized)."""
        if n1 == 0 or n2 == 0: return 0
        b1 = number_to_bitlist(n1)
        b2 = number_to_bitlist(n2)
        total_bits = [0]
        exponents1 = [i for i, bit in enumerate(b1) if bit == 1]
        exponents2 = [i for i, bit in enumerate(b2) if bit == 1]
        if not exponents1 or not exponents2: return 0
        for exp1 in exponents1:
            for exp2 in exponents2:
                new_exp = exp1 + exp2
                _add_sparse_inplace_primitive(total_bits, new_exp)
        return bitlist_to_number(total_bits)

    def _karatsuba_recursive(self, b1: List[int], b2: List[int]) -> List[int]:
        """Internal recursive part of Karatsuba."""
        len_b1 = len(b1) if any(b1) else 1
        len_b2 = len(b2) if any(b2) else 1
        n = max(len_b1, len_b2)

        if n <= 32: # Base case: switch to schoolbook for small numbers
            # Here, we call the CPU's schoolbook method, not the global one directly
            return number_to_bitlist(self._multiply_schoolbook(bitlist_to_number(b1), bitlist_to_number(b2)))

        m = (n + 1) // 2
        x0, x1 = b1[:m], b1[m:] if m < len(b1) else [0]
        y0, y1 = b2[:m], b2[m:] if m < len(b2) else [0]

        z2 = self._karatsuba_recursive(x1, y1)
        z0 = self._karatsuba_recursive(x0, y0)

        x1_plus_x0 = _add_primitive(x1, x0)
        y1_plus_y0 = _add_primitive(y1, y0)
        z1_intermediate = self._karatsuba_recursive(x1_plus_x0, y1_plus_y0)

        term_sub_z2 = _subtract_primitive(z1_intermediate, z2)
        middle_term = _subtract_primitive(term_sub_z2, z0)

        part1_shifted = _shift_primitive(z2, 2 * m)
        part2_shifted = _shift_primitive(middle_term, m)

        sum_part1_part2 = _add_primitive(part1_shifted, part2_shifted)
        final_result_bits = _add_primitive(sum_part1_part2, z0)

        while len(final_result_bits) > 1 and final_result_bits[-1] == 0:
            final_result_bits.pop()
        if not final_result_bits: return [0]
        return final_result_bits

    def _multiply_karatsuba(self, n1: int, n2: int) -> int:
        """Algorithm 3: The Karatsuba 'divide and conquer' algorithm."""
        if n1 == 0 or n2 == 0: return 0
        b1 = number_to_bitlist(n1)
        b2 = number_to_bitlist(n2)
        n_orig = max(len(b1) if any(b1) else 1, len(b2) if any(b2) else 1)
        n_padded = 1
        while n_padded < n_orig: n_padded <<= 1
        b1.extend([0] * (n_padded - len(b1)))
        b2.extend([0] * (n_padded - len(b2)))
        result_bits = self._karatsuba_recursive(b1, b2)
        return bitlist_to_number(result_bits)

    def intelligent_multiply(self, n1: int, n2: int) -> int:
        """
        Intelligently dispatches to the most efficient multiplication algorithm
        based on input characteristics.
        """
        if n1 == 0 or n2 == 0: return 0

        # Rule 0: Direct LUT lookup for small numbers
        # Check if both numbers are within the direct lookup range of the LUT
        # LUT_CHUNK_SIZE is 8, so limit is 1 << 8 = 256
        # This means numbers from 0 to 255 can be looked up directly.
        if n1 < (1 << self.LUT_CHUNK_SIZE) and n2 < (1 << self.LUT_CHUNK_SIZE):
            return self.lookup_table.get((n1, n2), n1 * n2) # Fallback to actual mult if somehow not in table (shouldn't happen)

        # Python 3.10+ for n.bit_count()
        # For older Python, use bin(n).count('1')
        try:
            n1_popcount = n1.bit_count()
            n2_popcount = n2.bit_count()
        except AttributeError: # Fallback for Python < 3.10
            n1_popcount = bin(n1).count('1')
            n2_popcount = bin(n2).count('1')

        max_bit_length = max(n1.bit_length(), n2.bit_length())

        # Rule 1: Karatsuba's Domain
        if max_bit_length > self.KARATSUBA_THRESHOLD_BITS:
            return self._multiply_karatsuba(n1, n2)

        # NEW Rule 1.5: Chunking LUT for moderate sizes if not caught by specific rules below
        # This rule is placed to allow specific niche algorithms (Schoolbook for dense*sparse, AoP for sparse*sparse)
        # to be chosen if their conditions are met, otherwise, for general numbers up to KARATSUBA_THRESHOLD_BITS,
        # use the chunking LUT.
        # The performance data suggests _multiply_lookup_table (chunking) is generally good
        # for numbers up to KARATSUBA_THRESHOLD_BITS in this Python simulation.

        # Rule 2: Schoolbook's Niche (Dense * Sparse)
        # Check if one is dense and the other is very sparse
        n1_is_dense = n1_popcount > (n1.bit_length() * self.DENSE_THRESHOLD_FACTOR)
        n2_is_dense = n2_popcount > (n2.bit_length() * self.DENSE_THRESHOLD_FACTOR)
        n1_is_very_sparse = n1_popcount <= self.SPARSE_POPCOUNT_THRESHOLD
        n2_is_very_sparse = n2_popcount <= self.SPARSE_POPCOUNT_THRESHOLD

        if (n1_is_dense and n2_is_very_sparse) or \
           (n2_is_dense and n1_is_very_sparse):
            return self._multiply_schoolbook(n1, n2)

        # Rule 3: AoP's Niche (Sparse * Sparse)
        if n1_is_very_sparse and n2_is_very_sparse:
            return self._multiply_aop_optimized(n1, n2)

        # Rule 4: Default for numbers up to KARATSUBA_THRESHOLD_BITS that don't meet specific niche criteria
        # Reverted to AoP_Optimized as the general default for this range, as LookupTable (chunking)
        # became slower than AoP after the "fairness" correction for its summation.
        return self._multiply_aop_optimized(n1, n2)

        # Old Rule for Chunking LUT Default:
        # return self._multiply_lookup_table(n1, n2)
        # This was based on the previous performance of _multiply_lookup_table before it used _add_primitive.
        # Now, AoP_Optimized is generally better than the "fair" _multiply_lookup_table for these sizes.

        # If we had another threshold above which Chunking LUT became worse than AoP (but still below Karatsuba),
        # then AoP could be a default for that specific intermediate range.
        # For now, LUT chunking seems to cover well up to Karatsuba's threshold.


# --- Standalone Complex Operations (can be moved into CPU or kept separate) ---
# For now, keeping them as module-level functions that can take any multiply_func.
# If they were CPU methods, they'd use self.intelligent_multiply or a specific one.

def power_integer(base_n: int, exponent_n: int, multiply_func: Callable[[int, int], int]) -> int:
    """
    Calculates base_n ^ exponent_n using the provided multiplication function.
    Uses exponentiation by squaring for efficiency.
    """
    if exponent_n < 0:
        raise ValueError("Exponent must be non-negative for integer power.")
    if exponent_n == 0: return 1
    if base_n == 0: return 0

    result = 1
    current_power = base_n
    while exponent_n > 0:
        if exponent_n % 2 == 1:
            result = multiply_func(result, current_power)
        current_power = multiply_func(current_power, current_power)
        exponent_n //= 2
    return result

def multiply_then_add(n1: int, n2: int, n3: int, multiply_func: Callable[[int, int], int]) -> int:
    """
    Calculates (n1 * n2) + n3 using the provided multiplication function
    and the internal _add_primitive.
    """
    product_n = multiply_func(n1, n2)
    product_bits = number_to_bitlist(product_n)
    n3_bits = number_to_bitlist(n3)
    sum_bits = _add_primitive(product_bits, n3_bits)
    return bitlist_to_number(sum_bits)

# --- For direct execution or testing of this module ---
if __name__ == '__main__':
    cpu = CPU()

    # Example usages:
    print("CPU Intelligent Multiply Examples:")
    print(f"5 * 7 = {cpu.intelligent_multiply(5, 7)}")

    # Karatsuba case
    n_large1 = (1 << 1025) - 12345
    n_large2 = (1 << 1025) - 67890
    print(f"Large1 * Large2 (expect Karatsuba): {cpu.intelligent_multiply(n_large1, n_large2)}")

    # Schoolbook case
    n_dense = (1 << 128) -1
    n_sparse_sb = 1 << 64
    print(f"Dense * Sparse (expect Schoolbook): {cpu.intelligent_multiply(n_dense, n_sparse_sb)}")

    # AoP Sparse * Sparse case
    n_sparse1_aop = 1 << 60
    n_sparse2_aop = 1 << 70
    print(f"Sparse * Sparse (expect AoP): {cpu.intelligent_multiply(n_sparse1_aop, n_sparse2_aop)}")

    # AoP Default case
    n_mid1 = random.randint(1 << 500, (1 << 512) -1)
    n_mid2 = random.randint(1 << 500, (1 << 512) -1)
    print(f"Mid-size random (expect AoP): {cpu.intelligent_multiply(n_mid1, n_mid2)}")

    print("\nStandalone Power and Multiply-Add Examples (using CPU's intelligent_multiply):")
    print(f"power_integer(3, 5, cpu.intelligent_multiply) = {power_integer(3, 5, cpu.intelligent_multiply)}")
    print(f"multiply_then_add(3, 5, 10, cpu.intelligent_multiply) = {multiply_then_add(3, 5, 10, cpu.intelligent_multiply)}")
