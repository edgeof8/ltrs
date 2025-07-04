# aopl_python_impl/aop_ai_explainer.py
#
# This module serves as the AI-powered explanation engine for the AoP calculator.
# It uses an AST-aware approach, building a detailed technical prompt by traversing
# the expression's syntax tree, then sends this to an AI to generate a coherent explanation.

import os
import requests
import json
from typing import Optional
from .aop_ast import ASTNode
from .aop_prompt_builder import PromptBuilderVisitor

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")  # Default to 'mistral' if not set

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/chat"

class AIConversation:
    """Manages the state of a conversation with the AI explainer."""
    def __init__(self, system_prompt: str, model: str):
        self.model = model
        self.history = [{"role": "system", "content": system_prompt.strip()}]

    def ask(self, user_prompt: str) -> str:
        """Sends a user prompt to the AI and returns the response."""
        self.history.append({"role": "user", "content": user_prompt.strip()})

        max_tokens = 4096
        try:
            if OPENROUTER_API_KEY:
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/placeholder-username/letter-powers",
                    "X-Title": "AoP Ltrs Calculator AI Explainer",
                }
                payload = {"model": self.model, "messages": self.history, "temperature": 0.2, "max_tokens": max_tokens}
                response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            else:  # Use Ollama
                payload = {"model": OLLAMA_MODEL, "messages": self.history, "temperature": 0.2}
                response = requests.post(OLLAMA_URL, json=payload, timeout=60)

            response.raise_for_status()
            response_data = response.json()

            if "choices" in response_data and response_data["choices"]:
                ai_response = response_data['choices'][0]['message']['content'].strip()
                self.history.append({"role": "assistant", "content": ai_response})
                return ai_response
            if "message" in response_data and "content" in response_data["message"]:
                ai_response = response_data['message']['content'].strip()
                self.history.append({"role": "assistant", "content": ai_response})
                return ai_response
            return f"Error: Unexpected response format: {response_data}"
        except requests.exceptions.RequestException as e:
            return f"Error: AI service connection failed: {e}"
        except Exception as e:
            return f"Error during AI call: {type(e).__name__}: {e}"


def get_ai_explanation_and_session(expression: str, result: str, base: int, ast: ASTNode) -> tuple[Optional[AIConversation], Optional[str]]:
    """
    Starts a new AI explanation session by building the initial prompt and getting the first response.
    Returns a conversation object and the initial explanation text.
    This uses a two-model approach: an "instructor" for the initial output and a "chatbot" for follow-ups.
    """
    if not OPENROUTER_API_KEY and not OLLAMA_MODEL:
        return None, "Error: No AI backend is configured. Please set either OPENROUTER_API_KEY or OLLAMA_MODEL."

    # Use a powerful model for both instruction and chat to ensure quality.
    instructor_model = "deepseek/deepseek-chat-v3-0324:free"
    chatbot_model = "deepseek/deepseek-chat-v3-0324:free" # Using a powerful chat model for follow-ups

    # 1. Use the PromptBuilderVisitor to generate a comprehensive, context-rich system prompt.
    builder = PromptBuilderVisitor(base=base)
    instructor_system_prompt = builder.build_prompt(ast)

    # 2. Create an "instructor" session to get the high-quality initial explanation.
    instructor_session = AIConversation(instructor_system_prompt, instructor_model)

    # 3. The user prompt simply asks the AI to perform its task.
    instructor_user_prompt = f"The expression to explain is `{expression}`. The final result was `{result}`. Please provide the explanation."
    initial_explanation = instructor_session.ask(instructor_user_prompt)

    # 4. Create the final "chatbot" session for the user, pre-loading it with the context.
    # The system prompt for the chatbot is simpler, focused on conversation.
    chat_system_prompt = f"You are a helpful AI assistant for the 'Alphabet of Powers' (AoP) calculator. An initial technical explanation of the user's calculation (`{expression}`) has been provided. Your job is to answer the user's follow-up questions clearly and concisely based on the conversation history."
    final_conversation = AIConversation(chat_system_prompt, chatbot_model)
    # Manually set the history to include the initial exchange.
    final_conversation.history = instructor_session.history

    return final_conversation, initial_explanation


def start_help_session() -> Optional[AIConversation]:
    """
    Starts a new AI conversation session for general help about the calculator.
    """
    if not OPENROUTER_API_KEY and not OLLAMA_MODEL:
        print("Error: No AI backend is configured. Please set either OPENROUTER_API_KEY or OLLAMA_MODEL.")
        return None

    # This system prompt defines the "Help" persona for the AI.
    help_system_prompt = """
You are "AoP Helper," a friendly and knowledgeable assistant for the "Alphabet of Powers" (AoP) command-line calculator.
Your purpose is to answer user questions about how to use the software, its syntax, its features, and the mathematical concepts behind it.

Key Features to be aware of:
- **Notation:** `a`=base^1, `b`=base^2, `Z`=base^100.
- **Literals:** `2c3a` is an additive polynomial: `(2*base^3) + (3*base^1)`.
- **Variables:** Defined with `$`, e.g., `$x = a+b`.
- **Operators:** `+`, `-`, `*`, `^`, `==`.
- **CLI Flags:** `--base`, `--mode`, `--debug`, `--explain`, `--ai-help`.
- **Symbolic Power:** The core concept is that `a^c` (base^1 to the power of 3) becomes `base^3`, which is `c`.
"""
    chatbot_model = "deepseek/deepseek-chat-v3-0324:free"
    return AIConversation(help_system_prompt, chatbot_model)
