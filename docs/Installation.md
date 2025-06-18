# Installation Guide

This guide covers installing the `ltrs` command-line tool and library.

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

- `matplotlib` (for graphing)
- `numpy` (numerical operations)
- `requests` (API communication)

### 4. Set OpenRouter API Key (Optional)

For AI explanations, obtain a key from [OpenRouter.ai](https://openrouter.ai/):

#### Linux/macOS

```bash
echo 'export OPENROUTER_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows (Command Prompt)

```cmd
setx OPENROUTER_API_KEY "your_api_key_here"
```

#### Windows (PowerShell)

```powershell
[System.Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY','your_api_key_here','User')
```

### 5. Verify Installation

```bash
ltrs --version
ltrs "a + b"  # Should output 110
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
pip install matplotlib numpy requests
```

**AI Explainer Errors:**

- Verify `OPENROUTER_API_KEY` is set
- Check network connection
- Ensure account has credits on OpenRouter

**Graphing Issues:**

- Install required dependencies: `pip install matplotlib numpy`
- On Linux, install system libraries: `sudo apt-get install python3-tk`

## Next Steps

- Explore the [[Usage Guide]] for detailed instructions
- Try [[Examples]] to see practical applications
- Learn about the [[AoP System Rules]]
