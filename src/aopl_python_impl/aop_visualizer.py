# aopl_python_impl/aop_visualizer.py

import matplotlib.pyplot as plt
import numpy as np
from .aop_calculator import AoP_Calculator as Calculator
from .definitions import ValueTuple

def plot_expression(
    calculator: Calculator,
    expression_str: str,
    variable_name: str,
    start_str: str,
    end_str: str,
    steps: int = 200,
    log_x: bool = False,
    log_y: bool = False
):
    """
    Evaluates an expression over a range and plots the result,
    with optional logarithmic scales.
    """
    try:
        start_val_tuple = calculator._evaluate_to_value_tuple(start_str)
        end_val_tuple = calculator._evaluate_to_value_tuple(end_str)

        start_num = start_val_tuple[0] * (calculator.base ** start_val_tuple[1])
        end_num = end_val_tuple[0] * (calculator.base ** end_val_tuple[1])

        if start_num >= end_num:
            print(f"Error: The start of the range ({start_num}) must be less than the end ({end_num}).")
            return

        if log_x and start_num <= 0:
            print(f"Error: Start of range ({start_num}) must be positive for a logarithmic x-axis.")
            return

        # Generate x_values: use logspace if log_x, otherwise linspace
        if log_x:
            # np.logspace needs log10 of start/end
            x_values = np.logspace(np.log10(start_num), np.log10(end_num), steps)
        else:
            x_values = np.linspace(start_num, end_num, steps)

        y_values = []
        original_var_value = calculator.variables.get(variable_name)

        for x_val in x_values:
            calculator.variables[variable_name] = (x_val, 0)
            try:
                result_tuple = calculator._evaluate_to_value_tuple(expression_str)
                y_num = result_tuple[0] * (calculator.base ** result_tuple[1])

                if log_y and y_num <= 0:
                    y_values.append(np.nan) # Cannot plot non-positive on log y-axis
                    print(f"Warning: Non-positive result ({y_num:.2f}) for {variable_name}={x_val:.2f} skipped for log y-axis.")
                else:
                    y_values.append(y_num)
            except Exception as e:
                print(f"Warning: Evaluation failed for {variable_name}={x_val:.2f} ({e}). Skipping point.")
                y_values.append(np.nan)

        if original_var_value is not None:
            calculator.variables[variable_name] = original_var_value
        else:
            if variable_name in calculator.variables:
                del calculator.variables[variable_name]

        # Convert y_values to numpy array for easier handling with nan
        y_values_np = np.array(y_values, dtype=float)

        plt.figure(figsize=(10, 6))

        # Choose plot type based on log flags
        if log_x and log_y:
            plt.loglog(x_values, y_values_np)
            plt.title(f"Graph of y = {expression_str} (Log-Log Scale)")
        elif log_x:
            plt.semilogx(x_values, y_values_np)
            plt.title(f"Graph of y = {expression_str} (Semi-Log X Scale)")
        elif log_y:
            plt.semilogy(x_values, y_values_np)
            plt.title(f"Graph of y = {expression_str} (Semi-Log Y Scale)")
        else:
            plt.plot(x_values, y_values_np)
            plt.title(f"Graph of y = {expression_str} (Linear Scale)")

        plt.xlabel(variable_name)
        plt.ylabel("Result")
        plt.grid(True, which="both", ls="-") # Grid for both major and minor ticks on log scales

        # Add horizontal/vertical lines only if not log scale or if origin is in view for log
        # For simplicity, let's always add them; matplotlib handles non-display if out of range.
        if not log_y: plt.axhline(0, color='black', linewidth=0.5)
        if not log_x: plt.axvline(0, color='black', linewidth=0.5)

        plt.show()

    except ImportError:
        print("Error: Matplotlib is required for graphing but not installed. Please run: pip install matplotlib")
    except Exception as e:
        print(f"An error occurred during graphing: {e}")
