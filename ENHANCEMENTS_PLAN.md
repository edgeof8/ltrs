# AoP Calculator - Enhancements Plan

This document outlines the next set of planned enhancements for the Alphabet of Powers (AoP) Python library and CLI, based on recent review and feedback.

## Phase 1 & 1B Enhancements (Completed)

(Content remains the same)

1.  **Performance Optimization for `aop_core.py`:**
    - Reusable, module-level `AoP_Calculator` instance with variable clearing for the stateless API.
2.  **Mathematical Extensions - Additional Logarithms:**
    - Support for `ln` (natural log) and `log2` (base-2 log) functions.
3.  **User Experience - Mathematical Constants (Expanded):**
    - Support for constants Pi (`#pi`, `π`, `#p`), Euler's number (`#e`, `#euler`, etc.), Golden Ratio (`#phi`, `φ`), Tau (`#tau`, `τ`), and Sqrt(2) (`#sqrt2`) using dedicated syntax.
4.  **Operator Expansion - Addition and Subtraction:**
    - Support for `+` and `-` operators (binary and unary), performing numerical addition/subtraction.
5.  **Type Safety - Interface Protocols (Initial Implementation & Refinement):**
    - `interfaces.py` created and protocols defined (including `CalculatorInterface`).
    - Ensured consistent `ValueTuple` definition for improved type checking.
    - `AoP_Calculator` implements `CalculatorInterface`.
    - `aop_core.py` uses `CalculatorInterface` for its shared instance.
6.  **Tokenizer Refinements:**
    - Improved handling of signed identifiers and operator disambiguation (e.g. for unary minus).

## Phase 2: Refinements & Feature Implementation (Incorporating Peer Review)

(Content remains the same)

### A. Code & Design Refinements (Mostly Completed):

1.  **Regex Definition Consolidation (from Peer Review) - (Completed):**

    - **Outcome:** `TERM_REGEX_PATTERN` removed; `aop_term_handler.py` now uses regex logic consistent with `TOKEN_SPECIFICATION`. Tokenizer logic for identifiers refined.

2.  **Clarity in `aop_formatter.py` (from Peer Review) - (Completed):**

    - **Outcome:** `format_output` function refactored; comments added to `represent_exponent_as_aop_term`.

3.  **Review `strip()` Usage (Minor - from Peer Review) - (Completed):**

    - **Outcome:** Logic in `AoP_Calculator._evaluate_to_value_tuple` simplified. Error handling for malformed assignments in `evaluate_expression` made more robust.

4.  **Test Granularity (Consolidation & Initial Split - Completed):**
    - **Outcome:** Created `test_aop_operations.py` and `test_aop_term_handler.py`. Some simple test cases in `test_aop_calculator.py` were consolidated.

### B. Feature Enhancements (Completed / In Progress):

1.  **Extended Mathematical Functionality - `sqrt` (Completed via User Feedback):**

    - **Outcome:** Implemented `sqrt` function. Handles `sqrt((coeff, expon))` as `(coeff**0.5, expon / 2)`.

2.  **Base Flexibility in CLI (Completed via User Feedback):**

    - **Outcome:** Implemented `/setbase <number>` command in the REPL (changed from `set base =`).

3.  **Extended Mathematical Functionality - Trigonometric Functions (Completed):**

    - **Outcome:** Implemented `sin()`, `cos()`, and `tan()` functions. Inputs are evaluated to numerical values (radians).

4.  **CLI Graphing Functionality (Completed):**

    - **Outcome:** Implemented `/graph <expr> for <var> from <start> to <end> [--logx] [--logy] [--loglog]` command in REPL using `matplotlib`. Supports linear and logarithmic scales.

5.  **Extended Mathematical Functionality - Inverse Trigonometric Functions (Completed):**

    - **Outcome:** Implemented `asin()`, `acos()`, and `atan()` functions. Added necessary domain checks for `asin` and `acos`.

6.  **Extended Mathematical Functionality - Hyperbolic Functions (Completed):**

    - **Outcome:** Implemented `sinh()`, `cosh()`, and `tanh()` functions. Added evaluation logic in `aop_parser.py`.

7.  **Parser Refactoring & Enhanced Error Reporting (Completed):**
    - **Outcome:** `aop_parser.py` refactored to use dispatch dictionaries for operator/function handling. `infix_to_rpn` enhanced for better syntactic validation. `AoPError` now provides detailed token-based error messages.

## Phase 3: Next Planned Steps (Continuing from Phase 2 Plan)

1.  **Enhanced Formatting/Unit Conversion (Completed):**

    - **Objective:** Provide more flexible and AoP-centric output formatting.
    - **Outcome:**
      - `normalize_value_tuple_for_display` function added to `aop_operations.py`.
      - `OutputFormatMode` enum (`auto`, `aop`, `scientific`, `numerical`) added to `definitions.py`.
      - `AoP_Calculator` now has an `output_format_mode` attribute.
      - `aop_formatter.format_output` signature updated and logic implemented for different modes.
      - `/setformat <mode>` command added to CLI.
      - Comprehensive unit tests for new formatting modes added and passing.
    - **To Do (Future):**
      - Consider "display value in different base" feature.

2.  **Extended Mathematical Functionality (Continued):**

    - **Complex Number Support (Major Extension):** Modify `ValueTuple`, update all operations, parsing, and formatting.
    - Graphing: "AoP Space" visualization (plotting ValueTuples directly).

3.  **Type Safety - Interface Protocols (Continued):**

    - **Objective:** Further enhance type safety.
    - **Approach:** Define more comprehensive protocols for other components if beneficial. `ValueNormalizerFunc` and `OutputFormatter` protocols updated.

4.  **Test Granularity (Continued):**

    - **Objective:** Create more separate test files and enhance test coverage.
    - **Progress:** `test_aop_parser.py`, `test_aop_formatter.py`, and `test_base_changes.py` created. Tests for formatting modes added.
    - **Next:** Add tests for `aop_visualizer.py` (may require mocking `matplotlib.pyplot`).

5.  **REPL Command Extensions (New):**
    - **Objective:** Enhance REPL usability and power with more slash commands.
    - **Completed:**
      - `/vars` or `/list`: Displays currently defined variables.
      - `/savevars [filename]`: Saves current variables to a JSON file.
      - `/loadvars [filename]`: Loads variables from a JSON file.
      - `/clear [var1 var2 ...]`: Clears specified variables, or all if none are given.
      - **AI Output Explanation (`/explain`)**: Integrate with a generative AI to explain calculation results.
      - `/setformat <mode>`: Configures output formatting style.
      - `/history [N]`: Shows the last N expressions (default 10).
    - **To Do (from brainstormed list - based on user feedback):**
      - Introspection/Debugging: `/showrpn <expr>`, `/tokenize <expr>`, `/evalas <format> <expr>`
      - Enhanced Graphing: `/bargraph <terms...>`, `/visualize <terms...>` (AoP Space)
      - File I/O & Scripting: `/run <filename.aop>`
      - REPL UX: Tab completion, Syntax highlighting (ANSI). (Moved `/history` to completed)
      - Informational: `/constants`, `/functions`, `/help <command>` (extend existing `/help`)

## Future Directions (Consolidated & Expanded from Peer Review)

(Incorporating user feedback)

- Educational Tool
- Publish to PyPI
- Web-Based Calculator / Visual Playground (e.g., Streamlit, PyScript)
- DSL Expansion
- Jupyter Integration
- Visualization (Basic function plotting with log scales implemented; "AoP Space" and other advanced options pending)
- API/Web Service
- Plugin Architecture
- Configuration Management
- Expression Caching
- Enhanced Documentation

---

This plan will guide the next development cycle.
