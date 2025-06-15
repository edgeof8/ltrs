# src/aopl_python_impl/aop_ai_explainer.py
import os
import requests
import json

# Environment variable for the API key
API_KEY_ENV_VAR = "OPENROUTER_API_KEY"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free" # Updated to user's specific free model ID

def get_explanation(expression: str, result: str, base: int, model: str = DEFAULT_MODEL) -> str:
    """
    Contacts an AI service to get an explanation for an AoP calculation.
    """
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        return (f"Error: AI Explainer feature requires an API key. "
                f"Please set the {API_KEY_ENV_VAR} environment variable.")

    system_prompt = f"""
You are an expert mathematician and computer scientist assisting a user of a special calculator called "The Alphabet of Powers" (AoP).
Your task is to provide a clear, concise, and insightful explanation for the result of a given calculation.

The AoP system works as follows:
- The base of the system is currently {base}.
- Letters 'a' through 'z' represent the base to the power of 1 through 26 respectively.
  - Example (base 10): a = 10^1, b = 10^2, c = 10^3, ..., z = 10^26.
- Words are multiplicative: 'cat' means c * a * t. In base 10, this is 10^3 * 10^1 * 10^20 = 10^(3+1+20) = 10^24, which is 'x'.
- Standard math operators (+, -, *, /, ^) and functions (sin, cos, tan, sqrt, log, ln, log2, asin, acos, atan, sinh, cosh, tanh) are supported.
- Special constants like #pi (π), #e (Euler's number), and #phi (φ, the Golden Ratio), #tau (τ), #sqrt2 exist.
- An output of 'AlphaZone(...)' means the number is too large for the a-z letter system (i.e., exponent > 26 for a coefficient of 1).
- An output of 'Unity(1)' represents the numerical value 1 (i.e., base^0).
- Numerical results are often preferred for simple numbers, but AoP letter form is used for values that fit the system.

Your explanation should:
1. Briefly state or confirm the result in plain terms if it's not obvious.
2. Explain the evaluation process, especially how AoP terms were interpreted and simplified according to the current base.
3. If applicable, highlight any interesting mathematical properties, provide context or scale for large/small numbers, or explain why an error might have occurred if the result indicates one.
4. Be encouraging, educational, and easy to understand. Avoid overly technical jargon unless necessary, and explain it if used.
5. If the expression is simple, keep the explanation concise. If complex, break it down.
"""

    user_prompt = f"The user entered the expression: `{expression}`\nThe calculator, with base {base}, returned the result: `{result}`\nPlease provide your explanation."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/placeholder-username/letter-powers",
        "X-Title": "AoP Ltrs Calculator AI Explainer"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        print("🤖 AI is thinking...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        response.raise_for_status()

        response_data = response.json()
        if 'choices' in response_data and response_data['choices']:
            explanation = response_data['choices'][0]['message']['content']
            return f"\n🤖 AI Explanation:\n{explanation.strip()}"
        else:
            return f"Error: AI service returned an unexpected response format: {response_data}"

    except requests.exceptions.Timeout:
        return "Error: The request to the AI service timed out."
    except requests.exceptions.HTTPError as http_err:
        return f"Error: AI service returned an HTTP error: {http_err} - Response: {response.text}"
    except requests.exceptions.RequestException as req_err:
        return f"Error: Could not connect to the AI service. ({req_err})"
    except KeyError:
        return f"Error: AI service returned an incomplete or malformed response: {response.json()}"
    except Exception as e:
        return f"An unexpected error occurred while getting the AI explanation: {type(e).__name__}"
    finally:
        pass

if __name__ == '__main__':
    if os.environ.get(API_KEY_ENV_VAR):
        print("Testing AI Explainer (this will make a real API call if key is valid):")

        test_expr = "100a * 10b"
        test_result_base10 = "f"
        print(f"\n--- Explaining: '{test_expr}' -> '{test_result_base10}' (base 10) ---")
        explanation1 = get_explanation(test_expr, test_result_base10, 10)
        print(explanation1)

        test_expr_2 = "cat / a"
        test_result_2_base10 = "w"
        print(f"\n--- Explaining: '{test_expr_2}' -> '{test_result_2_base10}' (base 10) ---")
        explanation2 = get_explanation(test_expr_2, test_result_2_base10, 10)
        print(explanation2)

        test_expr_3 = "a+b"
        test_result_3_base5 = "30"
        print(f"\n--- Explaining: '{test_expr_3}' -> '{test_result_3_base5}' (base 5) ---")
        explanation3 = get_explanation(test_expr_3, test_result_3_base5, 5)
        print(explanation3)
    else:
        print(f"{API_KEY_ENV_VAR} not set. Skipping live AI explainer test.")
