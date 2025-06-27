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
    *   `/constants`: Lists predefined numerical constants like `#pi`, `#e`, `#sqrt2`, and `#j`.
    *   `/letters`: Displays the current letter-to-exponent mapping for the active base.
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
- **Special Letter `z`**: `z` = `base^100` (and `Z` is an alias).

Words are formed by multiplication, with exponents adding together:
- **`cab`** (base 10) => `c*a*b` => `10^3 * 10^1 * 10^2` => `10^(3+1+2)` => `10^6`, which simplifies to **`f`**.

The engine can represent numbers as polynomials in this system, providing a unique "fingerprint" of their structure. For example, `2^10 = 1024` is represented as `c + 2a + 4` (`10^3 + 2*10^1 + 4`).

## III. The AoP Engine (CLI)

Underpinning the Cosmic Scratchpad is a robust command-line engine that can also be used independently for quick calculations.

**Engine Features:**

*   **Symbolic Core:** Represents all numbers as sparse polynomials (`AoPValue`), enabling arbitrary-precision arithmetic.
*   **Elegant Formatting:** Results are displayed in their most compact AoP form (e.g., `10^100` is `z`).
*   **Arbitrary Base:** Explore AoP in any integer base via the `--base` flag.
*   **Full Operator Support**: `+`, `-`, `*`, `/`, `^` (power), with correct order of operations.
*   **Implicit Multiplication:** Understands natural algebraic syntax like `2b` (2\*b) and `a(b+c)`.

**Command-Line Usage & Examples:**
```bash
# Assuming 'ltrs' alias is set up for the CLI script
# (See Installation section)

# Calculate 2 to the power of 1000
$ ltrs 2^c
10715086071862673209...

# Get the symbolic "fingerprint" of the result
$ ltrs 2^c --mode aop
a^301 + 7a^299 + ... + 7a + 6

# Symbolic representation of hyper-powers
$ ltrs a^k --base 2 --mode aop
a^(2c + 4a + 8)
# Explanation: In base 2, 'a' is 2. 'k' is 11. 2^11 = 2048.
# The number 2048 is then formatted as 2*10^3 + 4*10^1 + 8, or 2c+4a+8.
```

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/ltrs.git
    cd ltrs
    ```

2.  **(Recommended) Create a Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install PySide6 requests matplotlib numpy
    ```
    *   `PySide6` is required for the Cosmic Scratchpad GUI.
    *   `requests` is required for the AI Explainer feature.
    *   `matplotlib` and `numpy` are required for visualization features.

4.  **Set up AI Explainer (Optional):**
    The `/explain` command requires an AI backend. Configure one by setting an environment variable:
    *   **For OpenRouter:** `OPENROUTER_API_KEY="sk-or-..."`
    *   **For a local Ollama instance:** `OLLAMA_MODEL="mistral"` (or another model you have installed).

5.  **Set up CLI Alias (Optional):**
    For easy access to the command-line engine, create a `ltrs` alias.
    *   **Linux/macOS** (add to your `.bashrc` or `.zshrc`):
        ```bash
        alias ltrs='python -m src.aopl_python_impl.aop_calculator_cli'
        ```
    *   **Windows** (create a file named `ltrs.bat` in a folder that's in your system's PATH):
        ```batch
        @echo off
        python -m src.aopl_python_impl.aop_calculator_cli %*
        ```

## Project Structure

The project is organized into a primary GUI application and a core symbolic engine library.

-   `/` (Root Directory)
    -   `main.py`: Entry point for the Cosmic Scratchpad GUI.
    -   `cosmic_scene.py`: Manages all items, interactions, and command logic on the canvas.
    -   `gui_items.py`: Defines the custom QGraphicsItem classes for nodes, lines, etc.
    -   `config.py`: Contains configuration constants for the GUI.
    -   `README.md`: **This file.**
-   `/src/aopl_python_impl/`
    -   `aop_calculator.py`: The main calculator class that ties the engine together.
    -   `aop_value.py`: The core `AoPValue` class for sparse polynomial arithmetic.
    -   `aop_parser.py` & `aop_operations.py`: The parser and evaluation engine.
    -   `aop_formatter.py`: Logic for formatting results into `num` or `aop` strings.
    -   `aop_calculator_cli.py`: The entry point for the command-line tool.
    -   `aop_visualizer.py`, `aop_ai_explainer.py`, `aop_batch_processor.py`: Modules for advanced tooling.
-   `/research/`
    -   Contains numerous scripts and documents for performance profiling, experimentation, and theoretical exploration of the AoP system.
-   `/docs/`
    -   Detailed technical documentation on individual modules and concepts.
-   `/tests/`
    -   A suite of unit and integration tests to ensure the correctness of the engine.

## Contributing

Contributions, bug reports, and feature suggestions are highly welcome! Please feel free to open an issue or submit a pull request.
