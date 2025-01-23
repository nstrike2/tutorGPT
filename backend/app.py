import os
import re
import openai  # <-- Correct import statement
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the API key from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key.startswith("your_openai_api_key_here"):
    print("WARNING: No valid OpenAI API key found! "
          "Please set OPENAI_API_KEY in your .env file.")

openai.api_key = api_key


# ----------------------------------------------------
# 1. Enhanced Policy Checking for User Input
# ----------------------------------------------------
def is_violating_policy(user_message: str) -> bool:
    """
    A naive policy check. You could combine this with:
      - OpenAI Moderation endpoint
      - Regex for suspicious words/phrases
      - A dedicated classifier
    """
    blacklisted_phrases = [
        "give me the homework solution",
        "provide me the test answer",
        "help me cheat",
        "give me the code",
        "give me the answer",
        "malicious usage request",
    ]
    user_message_lower = user_message.lower()
    return any(phrase in user_message_lower for phrase in blacklisted_phrases)


# ----------------------------------------------------
# 2. Dynamic Filter for AI Output
# ----------------------------------------------------
def dynamic_filter(ai_response: str) -> str:
    """
    A multi-stage pipeline that tries to remove or redact
    any code snippets, direct solutions, or suspicious content.
    """

    # ---- Stage A: Remove code blocks (Markdown, HTML, etc.) ----
    # Example patterns for triple backticks or <code> tags
    code_block_pattern = re.compile(
        r"```[\s\S]*?```|<code>[\s\S]*?</code>", re.IGNORECASE)
    sanitized_response = code_block_pattern.sub(
        "[CODE REMOVED — Sorry, I cannot provide direct code.]", ai_response
    )

    # ---- Stage B: Redact suspicious lines if they look like code or a full solution. ----
    # For instance, lines that start with typical code patterns:
    # def, class, console prompts, includes 'import X', etc.
    suspicious_line_patterns = [
        r"^\s*(def\s+\w+\(|class\s+\w+|import\s+\w+)",     # Python
        r"^\s*(public\s+class|System\.out\.println)",      # Java
        r"^\s*#include\s*<\w+\.h>",                        # C/C++
        r"^\s*function\s+\w+\(|^\s*var\s+\w+\s*=",         # JavaScript
    ]
    for pattern in suspicious_line_patterns:
        sanitized_response = re.sub(
            pattern,
            "[LINE REMOVED — Sorry, I cannot provide direct code.]",
            sanitized_response,
            flags=re.MULTILINE
        )

    # ---- Stage C: Remove chain-of-thought or exact solutions. ----
    # This is naive: if the text includes "step by step solution" or "full solution".
    # You might refine with advanced heuristics or a separate AI model.
    solution_like_phrases = [
        "step by step solution",
        "full code",
        "complete solution",
    ]
    # For each phrase, we might replace it or disclaim it
    for phrase in solution_like_phrases:
        sanitized_response = re.sub(
            phrase,
            "[REDACTED — Not allowed to provide full solutions]",
            sanitized_response,
            flags=re.IGNORECASE
        )

    # ---- Stage D: Detect prompt injection or repeated attempts. ----
    # If you detect users repeatedly trying to circumvent filters,
    # you might store context in a session or block future requests.
    # We'll just do a naive example that if the text includes "ignore previous" or
    # "override your instructions," we replace with refusal:
    prompt_injection_pattern = re.compile(
        r"(ignore previous|override your instructions)", re.IGNORECASE)
    if prompt_injection_pattern.search(sanitized_response):
        sanitized_response = "I’m sorry, but I cannot deviate from policy."

    return sanitized_response


# ----------------------------------------------------
# 3. Chat API Endpoint
# ----------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Check if we have a valid API key
    if not api_key:
        return jsonify({"error": "No valid OpenAI API key configured"}), 500

    # Check for policy violation
    if is_violating_policy(user_message):
        return jsonify({
            "assistant_message": "I'm sorry, but I cannot help with that request."
        })

    # --- Call the chat completion API via OpenAI client ---
    try:
        system_instructions = (
            "You are Tutor++, an AI built for students of CS109. "
            "You behave like a TA in office hours: you explain concepts, "
            "offer guidance, and help students reason about problems. "
            "You do NOT provide fully written code solutions, nor do you "
            "provide direct answers to homework or tests. If a user asks "
            "for code or solutions directly, you must politely refuse. "
            "Offer explanations and hints (only when repeated attempts have been made) instead."
        )

        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_message}
            ],

        )
        ai_raw_response = completion["choices"][0]["message"]["content"].strip(
        )

        # Pass the raw AI output through our dynamic filter
        final_response = dynamic_filter(ai_raw_response)

    except Exception as e:
        print(f"Error calling OpenAI ChatCompletion: {e}")
        return jsonify({"error": "Failed to get response from model"}), 500

    return jsonify({"assistant_message": final_response}), 200


# ----------------------------------------------------
# In-memory store (replace with a real DB or logging system in prod)
ratings_log = []
# ----------------------------------------------------


# ----------------------------------------------------
# 4. Rating API Endpoint
# ----------------------------------------------------
@app.route("/api/rate", methods=["POST"])
def rate():
    """
    Store rating information for admin monitoring.
    """
    data = request.get_json()
    rating = data.get("rating")
    message_id = data.get("messageId")
    user_input = data.get("userInput")
    assistant_output = data.get("assistantOutput")

    # Log or save this entry; here we just append to a list
    entry = {
        "message_id": message_id,
        "rating": rating,
        "user_input": user_input,
        "assistant_output": assistant_output
    }
    ratings_log.append(entry)

    print(f"Rating received: {entry}")
    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
