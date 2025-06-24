# aopl_python_impl/aop_visualizer.py
# FIX: This entire module has been updated to work with the current AoPValue architecture.
# It was previously based on an outdated, simpler data model and was non-functional.
# It now correctly uses the calculator's evaluation pipeline to get numerical
# results for plotting.

import numpy as np
from .aop_calculator import AoP_Calculator as Calculator
from .aop_value import AoPValue, PracticalLimitError

# Moved matplotlib import inside the function to make it an optional dependency.
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
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: Matplotlib is required for graphing but not installed. Please run: pip install matplotlib")
        return

    try:
        # To evaluate start/end, we should use a clean variable context.
        # We store the calculator's current variables and restore them later.
        original_vars = calculator.variables.copy()
        calculator.variables.clear() # Clear for clean evaluation of range

        # Use the new evaluate_to_aop_value method to get raw values
        start_aop = calculator.evaluate_to_aop_value(start_str)
        end_aop = calculator.evaluate_to_aop_value(end_str)

        # Restore original variables for the main expression evaluation
        calculator.variables = original_vars

        start_num = start_aop.to_numerical(calculator.base)
        end_num = end_aop.to_numerical(calculator.base)

        if start_num.real >= end_num.real:
            print(f"Error: The start of the range ({start_num}) must be less than the end ({end_num}).")
            return

        if log_x and start_num.real <= 0:
            print(f"Error: Start of range ({start_num}) must be positive for a logarithmic x-axis.")
            return

        # Generate x_values: use logspace if log_x, otherwise linspace
        if log_x:
            # np.logspace needs log10 of start/end
            x_values = np.logspace(np.log10(start_num), np.log10(end_num), steps)
        else:
            x_values = np.linspace(start_num, end_num, steps)

        y_values = []
        # Store any pre-existing value for the plot variable to restore it later
        original_plot_var_value = calculator.variables.get(variable_name)

        for x_val in x_values:
            # Assign the current x value to the specified variable as an AoPValue
            calculator.variables[variable_name] = AoPValue.from_number(x_val)
            try:
                result_aop = calculator.evaluate_to_aop_value(expression_str)
                y_num = result_aop.to_numerical(calculator.base)

                if log_y and y_num.real <= 0:
                    y_values.append(np.nan) # Cannot plot non-positive on log y-axis
                    print(f"Warning: Non-positive result ({y_num:.2f}) for {variable_name}={x_val:.2f} skipped for log y-axis.")
                else:
                    y_values.append(y_num)
            except (PracticalLimitError, ValueError, TypeError, NotImplementedError, OverflowError) as e:
                print(f"Warning: Evaluation failed for {variable_name}={x_val:.2f} ({type(e).__name__}: {e}). Skipping point.")
                y_values.append(np.nan)

        # Restore the plot variable to its original state
        if original_plot_var_value is not None:
            calculator.variables[variable_name] = original_plot_var_value
        else:
            # If the variable didn't exist before, remove it
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

        if not log_y: plt.axhline(0, color='black', linewidth=0.5)
        if not log_x: plt.axvline(0, color='black', linewidth=0.5)

        plt.show()

    except Exception as e:
        print(f"An error occurred during graphing: {e}")
