# AoP Experimentation Guide

## Running ltrs Experiments

```bash
# Basic word evaluation
ltrs eval "cat"

# Operation testing
ltrs op "a * b"

# Base transformation
ltrs --base 2 eval "d"

# Output formats
ltrs --format symbolic eval "x / y"
```

## Output Conventions

1. Store raw results in `/ltrs_outputs/` directory
2. Name files using: `[date]_[experiment_type].txt`
3. Include command parameters in header comments

## Analysis Workflow

1. Run experiment series
2. Process results with Python analysis scripts
3. Visualize with matplotlib/PowerBI
4. Compare against theoretical predictions
