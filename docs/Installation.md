# Installation

This page guides you through installing the `ltrs` (Alphabet of Powers) command-line tool and library.

## Prerequisites

- **Python:** You need Python 3.9 or higher installed on your system. You can download it from [python.org](https://www.python.org/downloads/).
- **pip:** Python's package installer, which usually comes with Python.
- **Dependencies:** The project requires `matplotlib`, `numpy` (for graphing), and `requests` (for the AI explainer feature). These will be installed automatically by `pip` when you install `ltrs`.

## Installation Steps

1.  **Download or Clone the Project (If not installing from PyPI yet):**
    If you have the project files locally (e.g., cloned from a Git repository):
    Navigate to the root directory of the project (the one containing `pyproject.toml`).

2.  **Install `ltrs`:**
    From the project's root directory, install `ltrs` using `pip`. The recommended method for development is editable mode.

    - **Editable Mode (Recommended for Development):**
      This allows you to make changes to the source code and have them immediately reflected when you run `ltrs`, without needing to reinstall. It also installs all required dependencies.

      ```bash
      pip install -e .
      ```

    - **Standard Installation (Once published or for a stable local build):**
      If you were installing from a built wheel or a PyPI package (once available):
      ```bash
      # pip install ltrs  (from PyPI - not yet available)
      # or
      # pip install . (from local project root for a standard install)
      ```
      For now, using `pip install -e .` is the best approach with the local source code.

3.  **Set API Key for AI Explainer (Optional):**
    The `/explain` command uses an AI service (via OpenRouter) to provide explanations. To use this feature, you need to set an environment variable with your API key.

    - Obtain an API key from [OpenRouter.ai](https://openrouter.ai/).
    - Set the `OPENROUTER_API_KEY` environment variable. How to do this depends on your operating system:
      - **Linux/macOS (bash/zsh):**
        Add `export OPENROUTER_API_KEY="your_api_key_here"` to your shell profile (e.g., `~/.bashrc`, `~/.zshrc`) and source it, or set it for the current session.
      - **Windows (Command Prompt):**
        `set OPENROUTER_API_KEY=your_api_key_here` (for current session)
        `setx OPENROUTER_API_KEY "your_api_key_here"` (permanently, new command prompts will have it)
      - **Windows (PowerShell):**
        `$env:OPENROUTER_API_KEY="your_api_key_here"` (for current session)
        To set it permanently, search for "environment variables" in Windows settings.
    - If this variable is not set, the `/explain` command will show an error message prompting you to set it.

4.  **Verify Installation:**
    After installation, the `ltrs` command should be available in your terminal. Test it by running:
    ```bash
    ltrs --help
    ```
    This should display the help message for the `ltrs` tool. You can also try launching the REPL:
    ```bash
    ltrs
    ```

## Troubleshooting

- **`ltrs` command not found:**
  - Ensure your Python scripts directory is in your system's PATH. This is usually handled automatically by Python's installer and `pip`.
  - If you used a virtual environment, make sure it's activated.
  - Try restarting your terminal session.
- **`ImportError` for `matplotlib`, `numpy`, or `requests`:**
  - These should be installed automatically with `pip install -e .`. If not, you can try installing them manually: `pip install matplotlib numpy requests`.
- **`/explain` command errors:**
  - Ensure the `OPENROUTER_API_KEY` environment variable is correctly set and exported to your current terminal session.
  - Check your internet connection.
  - Verify your API key is valid and has credits/access on OpenRouter.

You should now be ready to use the `ltrs` calculator! Head over to the [[Usage]] page for details on how to use the CLI and REPL.
