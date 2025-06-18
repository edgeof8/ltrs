# aop_ai_explainer.py

Provides AI-powered explanations for expressions using OpenRouter API.

## Key Features

- Generates natural language explanations
- Uses GPT models via OpenRouter
- Handles complex expressions and hyper-operations
- Provides educational insights

## Implementation

### `AoPExplainer`

Main class for generating explanations.

#### Key Methods

- `__init__(self, api_key=None)`: Initialize with OpenRouter API key
- `explain_expression(self, expression: str)`: Generate explanation
- `_call_openrouter_api(self, prompt)`: Make API request

### Explanation Workflow

1. Format expression for the prompt
2. Create system message with AoP context
3. Generate prompt with expression
4. Call OpenRouter API
5. Parse and return response

## API Configuration

- Requires `OPENROUTER_API_KEY` environment variable
- Uses `openrouter` model by default
- Handles rate limiting and errors

## Example Usage

```python
from aopl_python_impl.aop_ai_explainer import AoPExplainer

explainer = AoPExplainer(api_key="your_api_key")
explanation = explainer.explain_expression("j^j^j")
print(explanation)
```

## Output Example

"This represents tetration: 10^10 raised to itself (10^10)^(10^10) = 10^(10^10 * 10^10) which simplifies to 10^(10^11). In AoP notation, this is represented as a^k."
