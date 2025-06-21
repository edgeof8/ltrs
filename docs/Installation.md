# Installation Guide

This guide covers installing the AoP Suite components: the `ltrs` command-line tool and the **Cosmic Scratchpad** graphical interface.

## Prerequisites

- **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
- **pip**: Python's package manager (included with Python)
- **Git** (optional): For cloning the repository

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/letter-powers.git
cd letter-powers
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
```

- **Linux/macOS**: `source venv/bin/activate`
- **Windows**: `venv\Scripts\activate`

### 3. Install Dependencies

```bash
pip install -e .
```

Core dependencies include:
- `PySide6` (required for Cosmic Scratchpad GUI)
- `matplotlib` (for graphing)
- `numpy` (numerical operations)
- `requests` (API communication)

### 4. Set API Keys (Optional)

For AI explanations, configure your preferred backend:

#### OpenRouter
```bash
# Linux/macOS
echo 'export OPENROUTER_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc

# Windows (Command Prompt)
setx OPENROUTER_API_KEY "your_api_key_here"

# Windows (PowerShell)
[System.Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY','your_api_key_here','User')
```

#### Local Ollama
```bash
# Linux/macOS
echo 'export OLLAMA_MODEL="model_name"' >> ~/.bashrc
source ~/.bashrc

# Windows (Command Prompt)
setx OLLAMA_MODEL "model_name"

# Windows (PowerShell)
[System.Environment]::SetEnvironmentVariable('OLLAMA_MODEL','model_name','User')
```

### 5. Verify Installation

#### Command-Line Tool
```bash
ltrs --version
ltrs "a + b"  # Should output 110
```

#### Cosmic Scratchpad GUI
```bash
python main.py  # Launches the graphical interface
```

## Configuration Options

### Output Precision
Set decimal precision in the REPL:
```bash
/setprecision 15
```

### Default Base
Change the numerical base:
```bash
/setbase 2
```

## Troubleshooting

### Common Issues

**`ltrs` command not found:**
- Ensure virtual environment is activated
- Check Python scripts directory is in PATH
- Reinstall package: `pip install -e .`

**Missing Dependencies:**
```bash
pip install PySide6 matplotlib numpy requests
```

**GUI Launch Issues:**
- Verify PySide6 installation: `pip show PySide6`
- Check system requirements for Qt: [Qt Documentation](https://doc.qt.io/qt-6/)
- On Linux, install system libraries: `sudo apt-get install libxcb-xinerama0`

**AI Explainer Errors:**
- Verify API keys are set correctly
- Check network connection
- Ensure account has credits on OpenRouter (if applicable)

**Graphing Issues:**
- Install required dependencies: `pip install matplotlib numpy`
- On Linux, install system libraries: `sudo apt-get install python3-tk`

## Next Steps
- Explore the [[Usage Guide]] for CLI instructions
- Learn about the [[Cosmic Scratchpad Guide]] for GUI usage
- Try [[Examples]] to see practical applications
- Review the [[AoP System Rules]] for core concepts
