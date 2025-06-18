import os
import requests
import json

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")  # Default to 'mistral' if not set
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/chat"

def get_explanation(expression: str, result: str, base: int, model: str = DEFAULT_MODEL) -> str:
    if not OPENROUTER_API_KEY and not OLLAMA_MODEL:
        return ("Error: No AI backend is configured. Please set either OPENROUTER_API_KEY or OLLAMA_MODEL.")

    system_prompt = f"""
You are an expert mathematician and computer scientist assisting a user of a special calculator called "The Alphabet of Powers" (AoP).
Your task is to provide a clear, concise, and insightful explanation for the result of a given calculation.

The AoP system works as follows:
- The base of the system is currently {base}.
- Letters 'a' through 'y' represent powers from base¹ to base²⁵.
- Letters 'A' through 'Y' represent powers from base²⁶ to base⁵⁰.
  - Example (base 10): a = 10^1, b = 10^2, ..., y = 10^25, A = 10^26, ..., Y = 10^50.
- Words are multiplicative: 'cat' means c * a * t. In base 10, that's 10^3 * 10^1 * 10^20 = 10^24, which is 'x'.
- Standard math operators (+, -, *, /, ^) and functions (sin, cos, tan, sqrt, log, ln, etc.) are supported.
- Special constants like #pi (π), #e (Euler’s number), #phi (φ), #tau (τ), #sqrt2 are recognized.
- 'AlphaZone(...)' means the number exceeds the representable letter range (i.e., exponent > 50).
- 'Unity(1)' means the result is 1 (i.e., base^0).
- Numerical output may be used for non-letterable or simpler results.

Your explanation should:
1. Confirm the result plainly if it’s not obvious.
2. Explain the AoP simplification process: how words are interpreted, how powers combine, etc.
3. Offer insight or context for very large or small values.
4. Be encouraging, clear, and educational. Explain jargon where used.
5. If the expression is simple, keep your explanation short. For complex cases, break it down step-by-step.
"""


    user_prompt = f"The user entered the expression: `{expression}`\nThe calculator, with base {base}, returned the result: `{result}`\nPlease provide your explanation."

    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()}
    ]

    try:
        print("🤖 AI is thinking...")

        if OPENROUTER_API_KEY:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/placeholder-username/letter-powers",
                "X-Title": "AoP Ltrs Calculator AI Explainer"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=25)

        else:  # Use Ollama
            payload = {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "temperature": 0.7
            }
            response = requests.post(OLLAMA_URL, json=payload, timeout=25)

        response.raise_for_status()
        response_data = response.json()

        # OpenRouter format
        if 'choices' in response_data and response_data['choices']:
            return "\n🤖 AI Explanation:\n" + response_data['choices'][0]['message']['content'].strip()

        # Ollama format
        if 'message' in response_data and 'content' in response_data['message']:
            return "\n🤖 AI Explanation:\n" + response_data['message']['content'].strip()

        return f"Error: Unexpected response format: {response_data}"

    except requests.exceptions.Timeout:
        return "Error: The request to the AI service timed out."
    except requests.exceptions.HTTPError as http_err:
        return f"Error: AI service returned an HTTP error: {http_err} - Response: {response.text}"
    except requests.exceptions.RequestException as req_err:
        return f"Error: Could not connect to the AI service. ({req_err})"
    except KeyError:
        return f"Error: Malformed response: {response.json()}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"
