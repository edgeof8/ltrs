from PySide6.QtGui import QPixmap
from aopl_python_impl.aop_calculator import AoP_Calculator

def generate_plot_pixmap(calculator, expression, variable, start_val, end_val, steps=200, log_x=False, log_y=False, width=400, height=300):
    """
    Generate a plot pixmap from the given expression and parameters.
    """
    try:
        import io
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Plotting needs matplotlib and numpy (pip install -e \".[gui]\").")
        return None

    try:
        temp_calc = AoP_Calculator(base=calculator.base)
        temp_calc.variables = calculator.variables.copy()

        start_num = float(temp_calc.evaluate_expression(start_val, "num")[0])
        end_num = float(temp_calc.evaluate_expression(end_val, "num")[0])

        if start_num >= end_num:
            return None
        if log_x and start_num <= 0:
            return None

        if log_x:
            x_values = np.logspace(np.log10(start_num), np.log10(end_num), steps)
        else:
            x_values = np.linspace(start_num, end_num, steps)

        y_values = []
        plot_var_key = f"${variable}"
        original_plot_var_value = temp_calc.variables.get(plot_var_key)

        for x_val in x_values:
            temp_calc.variables[plot_var_key] = temp_calc.evaluate_expression(str(int(x_val)), "num")[0]
            try:
                result_str, _ = temp_calc.evaluate_expression(expression, "num")
                y_num = float(result_str)
                if log_y and y_num <= 0:
                    y_values.append(np.nan)
                else:
                    y_values.append(y_num)
            except Exception:
                y_values.append(np.nan)

        if original_plot_var_value is not None:
            temp_calc.variables[plot_var_key] = original_plot_var_value
        elif plot_var_key in temp_calc.variables:
            del temp_calc.variables[plot_var_key]

        y_values_np = np.array(y_values, dtype=float)
        plt.figure(figsize=(width/100, height/100-0.3))
        plot_func = plt.plot
        if log_x and log_y:
            plot_func = plt.loglog
        elif log_x:
            plot_func = plt.semilogx
        elif log_y:
            plot_func = plt.semilogy

        plot_func(x_values, y_values_np)
        plt.grid(True, which="both", ls="-")
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        plt.close()
        return pixmap
    except ImportError:
        return None
    except Exception as e:
        print(f"Error generating plot: {e}")
        return None
