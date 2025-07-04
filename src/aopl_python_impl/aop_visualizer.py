# aopl_python_impl/aop_visualizer.py
#
# This module provides an optional graphing utility for visualizing AoP expressions
# over a range of values for a given variable. It uses matplotlib for plotting.
from __future__ import annotations
from typing import Optional

from .aop_calculator import AoP_Calculator

# Moved matplotlib import inside the function to make it an optional dependency.
def plot_expression(
    calculator: AoP_Calculator,
    expression_str: str,
    variable_name: str,
    start_str: str,
    end_str: str,
    steps: int = 200,
    log_x: bool = False,
    log_y: bool = False,
):
    """
    Evaluates an expression over a range and plots the result,
    with optional logarithmic scales.
    """
    # These are heavy dependencies, so we import them only when the function is called.
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Error: Matplotlib and NumPy are required for graphing. Please run: pip install matplotlib numpy")
        return

    try:
        # Use a temporary, clean calculator instance to evaluate the plot bounds
        # without interference from the main calculator's variable state.
        temp_calc_for_bounds = AoP_Calculator(base=calculator.base)

        start_str_res, _ = temp_calc_for_bounds.evaluate_expression(start_str)
        end_str_res, _ = temp_calc_for_bounds.evaluate_expression(end_str)

        start_num = int(start_str_res)
        end_num = int(end_str_res)

        if start_num >= end_num:
            print(f"Error: The start of the range ({start_num}) must be less than the end ({end_num}).")
            return

        if log_x and start_num <= 0:
            print(f"Error: Start of range ({start_num}) must be positive for a logarithmic x-axis.")
            return

        # Generate x-axis values: use logspace if log_x, otherwise linspace
        if log_x:
            x_values = np.logspace(np.log10(start_num), np.log10(end_num), steps)
        else:
            x_values = np.linspace(start_num, end_num, steps)

        y_values = []
        # Store any pre-existing value for the plot variable to restore it later
        plot_var_key = f"${variable_name}" # Variables are referenced with a '$' prefix
        original_plot_var_value = calculator.variables.get(plot_var_key)

        for x_val in x_values:
            # Assign the current x value to the specified variable as an AoPValue
            calculator.variables[plot_var_key] = AoPValue.from_number(int(x_val), calculator.base)
            try:
                result_str, _ = calculator.evaluate_expression(expression_str, mode="num")
                y_num = float(result_str)

                if log_y and y_num <= 0:
                    y_values.append(np.nan) # Cannot plot non-positive on log y-axis
                    print(f"Warning: Non-positive result ({y_num:.2f}) for {variable_name}={x_val:.2f} skipped for log y-axis.")
                else:
                    y_values.append(y_num)
            except (ValueError, TypeError, NotImplementedError, OverflowError, NameError) as e:
                print(f"Warning: Evaluation failed for {variable_name}={x_val:.2f} ({type(e).__name__}: {e}). Skipping point.")
                y_values.append(np.nan)

        # Restore the plot variable to its original state
        if original_plot_var_value is not None:
            calculator.variables[plot_var_key] = original_plot_var_value
        else:
            # If the variable didn't exist before, remove it
            if plot_var_key in calculator.variables:
                del calculator.variables[plot_var_key]

        # Convert y_values to numpy array for easier handling with nan
        y_values_np = np.array(y_values, dtype=float)

        plt.figure(figsize=(10, 6))

        plot_func = plt.plot
        if log_x and log_y: plot_func = plt.loglog
        elif log_x: plot_func = plt.semilogx
        elif log_y: plot_func = plt.semilogy

        plot_func(x_values, y_values_np)
        plt.title(f"Graph of y = {expression_str}")
        plt.ylabel("Result")
        plt.grid(True, which="both", ls="-")
        plt.show()
    except Exception as e:
        print(f"An error occurred during graphing: {e}")
