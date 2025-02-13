import os
import re
import openai
import logging
import redis
import json
from typing import Any, Dict, List
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import config  # Import our configuration settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set OpenAI API key from config
if not config.OPENAI_API_KEY or config.OPENAI_API_KEY.startswith("your_openai_api_key_here"):
    logger.warning(
        "No valid OpenAI API key found! Please set OPENAI_API_KEY in your .env file.")
openai.api_key = config.OPENAI_API_KEY

# Initialize Flask and configure it to serve the frontend build
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), '../frontend/build'),
    static_url_path=''
)

CORS(app)  # Enable CORS for all routes


# Set up Redis client
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=0,
    decode_responses=True  # so we get string outputs instead of bytes
)

# ----------------------------------------------------
# Serve the Frontend
# ----------------------------------------------------


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# ----------------------------------------------------
# Guardrail: Basic Rate Limiting per IP
# ----------------------------------------------------


def rate_limit_exceeded(ip: str, limit_seconds: int = 5) -> bool:
    """
    Returns True if the client (identified by IP) has made a request
    within the last `limit_seconds` seconds.
    """
    key = f"rate:{ip}"
    if redis_client.exists(key):
        return True
    else:
        # Set a key with an expiration time
        redis_client.set(key, 1, ex=limit_seconds)
        return False

# ----------------------------------------------------
# Helper functions for conversation history using Redis
# ----------------------------------------------------


def get_conversation_history() -> List[Dict[str, str]]:
    history = redis_client.get("conversation_history")
    if history:
        return json.loads(history)
    return []


def save_conversation_history(history: List[Dict[str, str]]) -> None:
    redis_client.set("conversation_history", json.dumps(history))

# ----------------------------------------------------
# 1. Enhanced Policy Checking for User Input
# ----------------------------------------------------


def is_violating_policy(user_message: str) -> bool:
    """
    Checks for blacklisted phrases and prompt injection attempts.
    """
    blacklisted_phrases = [
        "give me the homework solution",
        "provide me the test answer",
        "help me cheat",
        "give me the code",
        "give me the answer",
        "malicious usage request",
    ]
    # Also check for prompt injection attempts in the user message
    injection_phrases = [
        "ignore previous",
        "override your instructions",
    ]
    message_lower = user_message.lower()
    if any(phrase in message_lower for phrase in blacklisted_phrases):
        return True
    if any(phrase in message_lower for phrase in injection_phrases):
        return True
    return False

# ----------------------------------------------------
# 2. Dynamic Filter for AI Output
# ----------------------------------------------------


def dynamic_filter(ai_response: str) -> str:
    """
    A multi-stage pipeline that tries to remove or redact
    any code snippets, direct solutions, or suspicious content.
    """
    # Stage A: Remove code blocks (Markdown, HTML, etc.)
    code_block_pattern = re.compile(
        r"```[\s\S]*?```|<code>[\s\S]*?</code>", re.IGNORECASE)
    sanitized_response = code_block_pattern.sub(
        "[CODE REMOVED — Sorry, I cannot provide direct code.]", ai_response
    )

    # Stage B: Redact suspicious lines that look like code
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

    # Stage C: Remove phrases that indicate a full solution
    solution_like_phrases = [
        "step by step solution",
        "full code",
        "complete solution",
    ]
    for phrase in solution_like_phrases:
        sanitized_response = re.sub(
            phrase,
            "[REDACTED — Not allowed to provide full solutions]",
            sanitized_response,
            flags=re.IGNORECASE
        )

    # Stage D: Detect prompt injection attempts in the AI response (redundant but extra safety)
    prompt_injection_pattern = re.compile(
        r"(ignore previous|override your instructions)", re.IGNORECASE)
    if prompt_injection_pattern.search(sanitized_response):
        sanitized_response = "I’m sorry, but I cannot deviate from policy."

    return sanitized_response


# ----------------------------------------------------
# Discrete Functions for the Chat Endpoint
# ----------------------------------------------------
MAX_MESSAGE_LENGTH = 1000  # Maximum allowed length for user messages


def validate_request(data: Dict[str, Any]) -> str:
    """
    Validate incoming request data and extract the user message.
    Raises ValueError if the message is missing or too long.
    """
    user_message = data.get("message", "").strip()
    if not user_message:
        raise ValueError("Message is required")
    if len(user_message) > MAX_MESSAGE_LENGTH:
        raise ValueError("Message is too long. Please shorten your message.")
    return user_message


def prepare_messages(user_message: str) -> List[Dict[str, str]]:
    """
    Prepare the messages list for the OpenAI ChatCompletion API.
    Retrieves conversation history from Redis, appends the new user message,
    and returns a list with system instructions followed by the conversation.
    """
    # Retrieve current conversation history from Redis
    history = get_conversation_history()
    # Append user message to the conversation history
    history.append({"role": "user", "content": user_message})
    save_conversation_history(history)

    system_instructions = (
        "You are Tutor++, an AI-powered tutoring assistant designed to help students in CS109 while upholding academic integrity. "
        "Your role is to provide guidance as a TA during office hours: you are patient, approachable, and dedicated to uncovering each student's thought process. "
        "Your goal is to help students build problem-solving skills, promote independent learning, and develop confidence through critical thinking. "
        "\n\n"
        "SPECIFIC TEACHING STRATEGIES:\n"
        "- Use Socratic questioning: Ask thoughtful, open-ended questions (e.g., 'What have you tried so far?' or 'Why do you think that approach didn’t work?') to encourage students to think deeply and arrive at answers independently.\n"
        "- Employ scaffolding: Break down complex problems into manageable steps, guiding students step-by-step without providing complete solutions.\n"
        "- Encourage metacognition: Prompt students to reflect on their learning process by asking questions like 'What strategy did you find most helpful here?' or 'What would you do differently next time?'.\n"
        "- Use real-world analogies: Relate abstract or complex concepts to familiar, real-life scenarios to make them more concrete and memorable.\n\n"
        "EXPLICIT BOUNDARIES ON THE AI'S ROLE:\n"
        "- Never provide full solutions, final code, or direct answers to assignments. Instead, offer hints, pseudocode, and conceptual explanations.\n"
        "- Remain within the CS109 academic scope. If a request is off-topic (e.g., personal advice or non-CS109 topics), politely redirect or decline to answer.\n"
        "- If a student repeatedly requests disallowed content, firmly remind them of academic integrity policies and encourage them to work through the problem with guidance.\n\n"
        "HANDLING AMBIGUOUS OR EDGE-CASE REQUESTS:\n"
        "- When faced with vague or ambiguous questions, ask clarifying questions before providing guidance.\n"
        "- If the conversation drifts from the original problem, confirm whether the student intends to switch topics. Only proceed with the new focus if it is explicitly requested and remains within the academic scope.\n"
        "- Always use all the provided context when answering questions and avoid straying from your initial prompt unless the student explicitly asks for a change.\n\n"
        "RESPONSE FORMATTING AND CLARITY:\n"
        "- Structure explanations in clear, logical steps (e.g., 'Step 1: Understand the Problem', 'Step 2: Break Down the Components').\n"
        "- Use bullet points or numbered lists for multi-part explanations.\n"
        "- Keep responses concise yet thorough, avoiding unnecessary jargon and ensuring clarity for students at different levels.\n"
        "- Format key terms in bold or italics as needed and include code blocks for code snippets.\n\n"
        "ENGAGEMENT, PERSONALIZATION, AND INCLUSIVITY:\n"
        "- Adapt explanations based on the student’s level of understanding: use simpler language for beginners and more technical details for advanced students.\n"
        "- Provide encouragement and positive reinforcement throughout the learning process.\n"
        "- Use inclusive, respectful language that avoids stereotypes and welcomes students from diverse backgrounds.\n"
        "- Whenever possible, relate problems to diverse, real-world contexts to increase relevance and engagement.\n\n"
        "GENERAL REMINDERS:\n"
        "- Always use all the context provided when answering questions. Never stray from your prompt or drift from the initial focus unless directly requested to, or unless a new problem is explicitly given.\n"
        "- If you are unsure about what is being asked, ask the user for clarification rather than guessing.\n\n"
        "Your ultimate objective is to guide students through the problem-solving process without giving away answers, helping them build independent learning skills while maintaining academic integrity."
    )

    messages = [{"role": "system", "content": system_instructions}]
    messages.extend(history)
    return messages


def call_gpt_api(messages: List[Dict[str, str]]) -> str:
    """
    Interact with the OpenAI ChatCompletion API and return the raw AI response.
    """
    try:
        completion = openai.ChatCompletion.create(
            model=config.MODEL_NAME,
            messages=messages
        )
        ai_response = completion["choices"][0]["message"]["content"].strip()
        return ai_response
    except Exception as e:
        logger.error("Error calling OpenAI API: %s", e)
        raise


def format_response(raw_response: str) -> str:
    """
    Apply dynamic filtering to the raw API response.
    """
    return dynamic_filter(raw_response)

# ----------------------------------------------------
# Chat API Endpoint
# ----------------------------------------------------


@app.route("/api/chat", methods=["POST"])
def chat() -> Response:
    # Basic rate limiting based on client IP address
    client_ip = request.remote_addr or "unknown"
    if rate_limit_exceeded(client_ip):
        return jsonify({"error": "Too many requests. Please slow down."}), 429

    data = request.get_json() or {}
    try:
        user_message = validate_request(data)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    # Enforce policy check
    if is_violating_policy(user_message):
        return jsonify({"assistant_message": "I'm sorry, but I cannot help with that request."})

    messages = prepare_messages(user_message)

    try:
        raw_response = call_gpt_api(messages)
        final_response = format_response(raw_response)
    except Exception:
        return jsonify({"error": "Failed to get response from model"}), 500

    # Retrieve conversation history, append assistant message, and save back
    history = get_conversation_history()
    history.append({"role": "assistant", "content": final_response})
    save_conversation_history(history)

    return jsonify({"assistant_message": final_response}), 200


# ----------------------------------------------------
# Rating API Endpoint
# ----------------------------------------------------
ratings_log: List[Dict[str, Any]] = []  # In-memory store for ratings


@app.route("/api/rate", methods=["POST"])
def rate() -> Response:
    """
    Store rating information for admin monitoring.
    """
    data = request.get_json() or {}
    entry = {
        "message_id": data.get("messageId"),
        "rating": data.get("rating"),
        "user_input": data.get("userInput"),
        "assistant_output": data.get("assistantOutput")
    }
    ratings_log.append(entry)
    logger.info("Rating received: %s", entry)
    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
