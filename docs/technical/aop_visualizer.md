# aop_visualizer.py

Implements graphing functionality for AoP expressions using matplotlib and numpy.

## Key Features

- 2D and 3D function plotting
- Support for real and complex domains
- Configurable ranges and resolutions
- Logarithmic scale options
- Interactive visualization

## Key Classes

### `AoPVisualizer`

Main class for creating plots.

#### Key Methods

- `plot_2d(expression, x_range, y_range)`: 2D function plot
- `plot_3d(expression, x_range, y_range)`: 3D surface plot
- `plot_complex(expression, real_range, imag_range)`: Complex domain visualization
- `show()`: Display plot

## Plot Types

1. **2D Functions**:
   - `plot_2d("x^2", (-5, 5))`
2. **3D Surfaces**:
   - `plot_3d("x^2 + y^2", (-5,5), (-5,5))`
3. **Complex Domains**:
   - `plot_complex("sqrt(z)", (-5,5), (-5,5))`

## Configuration Options

- `title`: Plot title
- `xlabel`, `ylabel`: Axis labels
- `logx`, `logy`: Logarithmic scales
- `colormap`: Color scheme for 3D plots
- `resolution`: Sampling density

## Example Usage

```python
from aopl_python_impl.aop_visualizer import AoPVisualizer

viz = AoPVisualizer()
viz.plot_2d("b^x", (0, 3), title="Exponential Growth")
viz.show()
```

## Dependencies

- matplotlib
- numpy
- mpl_toolkits (for 3D plots)
