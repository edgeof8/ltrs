
# Cosmic Scratchpad & The Alphabet of Powers Engine

Welcome to the Alphabet of Powers (AoP) project, a suite featuring a powerful symbolic algebra engine and the **Cosmic Scratchpad**—an innovative, node-based graphical environment for exploring numbers of all scales, from the everyday to the truly astronomical.

This is more than just a calculator; it's a visual tool for exploring number theory, symbolic algebra, and the very limits of computation in an interactive, infinite canvas.


*(A sample session showing variable dependencies, slash commands, and calculations.)*

## I. The Cosmic Scratchpad GUI

The Cosmic Scratchpad is the heart of the project—an interactive, graphical environment for AoP calculations and mathematical exploration.

**Key Features:**

*   **Infinite Canvas:** A zoomable, pannable canvas to lay out your thoughts, connect ideas, and build complex calculations visually.
*   **Live Calculation Nodes:**
    *   Click anywhere to create a new calculation node. Results update live as you type.
    *   **Multi-line Scripts:** Use `Shift+Enter` for new lines to write sequential statements within a single node.
    *   **Variable Assignments:** Define variables like `$myvar = a*b` and use them in other nodes.
    *   **Automatic Dependency Graph:** Nodes automatically update when variables they depend on change, creating a reactive calculation environment.
    *   **Resizable Nodes with Auto-Font:** Drag a node's corner to resize it. The font size automatically adjusts to fit the new bounds!
*   **Drawing & Annotation Tools:**
    *   **Line Tool:** Draw lines to connect ideas or highlight relationships.
    *   **Text Note Tool:** Add non-calculating text annotations to your canvas. Also resizable with auto-sizing fonts.
    *   **Pen Tool:** Freehand draw for sketches, diagrams, or emphasis.
*   **Interactive Base Changing:** Instantly change the numerical base for the entire scratchpad and watch all calculations update in real-time.
*   **Powerful Slash Commands:**
    *   `/help`: Shows available commands.
    *   `/vars`: Lists all defined variables and their current values.
    *   `/constants`: Lists predefined numerical constants like `#pi`, `#e`, `#sqrt2`, and `#j` (the imaginary unit).
    *   `/letters` or `/aopabet`: Displays the current letter-to-exponent mapping for the active base.
    *   `/setbase <num>`: Changes the calculator base for the entire scene.
    *   `/delvar <$var>`: Deletes a variable and updates dependent nodes.
    *   `/explain [expr|last]`: Provides an AI-generated explanation for an expression or the last calculation (requires setup).
    *   `/explain model <name>`: Sets the AI model for explanations (e.g., a local Ollama model or an OpenRouter model).
*   **File Operations:** Save and load your scratchpad sessions as `.cosmic` JSON files.

**Running the Cosmic Scratchpad:**
```bash
python main.py
```

## II. The Alphabet of Powers (Core Concept)

The AoP system provides a novel, compact way to represent and manipulate numbers, especially very large ones. By default, it operates in base 10.

- **Lowercase `a-y`**: `a` = `base^1`, `b` = `base^2`, ..., `y` = `base^25`.
- **Uppercase `A-Y`**: `A` = `base^26`, `B` = `base^27`, ..., `Y` = `base^50`.
- **Special Letter `Z`**: `Z` = `base^100`. The lowercase `z` is a convenient alias for `Z`.

Words are formed by multiplication, with exponents adding together:
- **`cab`** (base 10) => `c*a*b` => `10^3 * 10^1 * 10^2` => `10^(3+1+2)` => `10^6`, which simplifies to **`f`**.
- **`aZ`** (base 10) => `a*Z` => `10^1 * 10^100` => `10^101`. The formatter simplifies this to **`a^101`** or a similar symbolic form.

## III. The AoP Engine (CLI)

Underpinning the Cosmic Scratchpad is a robust command-line engine that can also be used independently for quick calculations.

**Engine Features:**

*   **Numeric-First, Symbolic-Fallback:** The engine uses a high-precision (`200` digits) `Decimal` backend to perform numerical calculations whenever possible. For hyper-powers or complex symbolic expressions that would overflow, it gracefully falls back to a symbolic representation.
*   **Elegant Formatting:** Results are displayed in their most compact AoP form (e.g., `10^100` is `Z`).
*   **Arbitrary Base:** Explore AoP in any integer base via the `--base` flag.
*   **Full Operator Support**: `+`, `-`, `*`, `/`, `==` (equality), and `^` (power), with correct order of operations (right-associativity for `^`).
*   **Implicit Multiplication:** Understands natural algebraic syntax like `2b` (2\*b) and `a(b+c)` (a\*(b+c)).
*   **Built-in Constants**: `#pi`, `#e`, `#phi`, `#tau`, `#sqrt2`, `#j`, `#sqrt3`, `#ln2`.

**Command-Line Usage & Examples:**

```bash
# Assuming 'ltrs' alias is set up for the CLI script
# (See Installation section)

# Simple multiplication and simplification
$ ltrs "cab"
f

# Hyper-powers and symbolic fallback
$ ltrs "3^3^3^3"
a^3638334640024

# Symbolic representation of massive numbers
$ ltrs "b^b^b"
a^(2*Z^2)
# Explanation: b^(b^b) -> (10^2)^((10^2)^(10^2)) -> 10^(2 * 10^200) -> a^(2*(10^100)^2) -> a^(2*Z^2)

# Coefficient absorption in a different base
$ ltrs --base 2 "2d"
e
# Explanation: In base 2, '2' is 'a' (2^1) and 'd' is 2^4. So, 2 * 2^4 = 2^5, which is 'e'.
```

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **(Recommended) Create a Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install PySide6 requests matplotlib
    ```
    *   `PySide6` is required for the Cosmic Scratchpad GUI.
    *   `requests` is required for the AI Explainer feature.
    *   `matplotlib` is required for visualization features (currently in `aop_visualizer.py`).

4.  **Set up AI Explainer (Optional):**
    The `/explain` command requires an AI backend. Configure one by setting an environment variable:
    *   **For OpenRouter:** `OPENROUTER_API_KEY="sk-or-..."`
    *   **For a local Ollama instance:** `OLLAMA_MODEL="mistral"` (or another model you have installed).

5.  **Set up CLI Alias (Optional):**
    For easy access to the command-line engine, create a `ltrs` alias.
    *   **Linux/macOS** (add to your `.bashrc` or `.zshrc`):
        ```bash
        alias ltrs='python -m aopl_python_impl.aop_calculator_cli'
        ```
    *   **Windows** (create a file named `ltrs.bat` in a folder that's in your system's PATH):
        ```batch
        @echo off
        python -m aopl_python_impl.aop_calculator_cli %*
        ```

## Development & Future Ideas

The AoP suite is an evolving project. Potential future directions include:
*   Integrating the `aop_visualizer` to allow graphing functions directly on the canvas.
*   More advanced drawing tools (shapes, arrows, color pickers).
*   User-defined functions within the AoP syntax.
*   Enhanced numerical simplification rules (e.g., for sums like `a+a` -> `2a`).
*   Exporting the scratchpad canvas to image/PDF formats.

## Contributing

Contributions, bug reports, and feature suggestions are highly welcome! Please feel free to open an issue or submit a pull request.
