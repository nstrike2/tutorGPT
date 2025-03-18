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
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set OpenAI API key from config
if not config.OPENAI_API_KEY or config.OPENAI_API_KEY.startswith(
    "your_openai_api_key_here"
):
    logger.warning(
        "No valid OpenAI API key found! Please set OPENAI_API_KEY in your .env file."
    )
openai.api_key = config.OPENAI_API_KEY

# Initialize Flask and configure it to serve the frontend build
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "../frontend/build"),
    static_url_path="",
)

# Set up CORS for API routes
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "https://tutorgpt.onrender.com"]
        }
    },
)

# Ensure all responses include CORS headers (even on errors)


@app.after_request
def add_cors_headers(response):
    allowed_origins = ["http://localhost:3000", "https://tutorgpt.onrender.com"]
    origin = request.headers.get("Origin")
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = (
            "https://tutorgpt.onrender.com"
        )
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.errorhandler(500)
def handle_500_error(e):
    response = jsonify({"error": "Internal Server Error", "details": str(e)})
    origin = request.headers.get("Origin")
    allowed_origins = ["http://localhost:3000", "https://tutorgpt.onrender.com"]
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = (
            "https://tutorgpt.onrender.com"
        )
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response, 500


# Set up Redis client
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=0,
    decode_responses=True,  # so we get string outputs instead of bytes
)


# ----------------------------------------------------
# Serve the Frontend
# ----------------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


# ----------------------------------------------------
# Guardrail: Enhanced Rate Limiting per IP
# ----------------------------------------------------


def rate_limit_exceeded(ip: str) -> bool:
    """
    Enhanced rate limiting using Redis to track requests per IP.
    Returns True if the client has exceeded the rate limit.
    """
    key = f"rate:{ip}"
    pipe = redis_client.pipeline()

    # Get current count and increment
    current = redis_client.get(key)
    if current is None:
        # First request - set initial count and expiry
        pipe.set(key, 1)
        pipe.expire(key, config.RATE_LIMIT_SECONDS)
        pipe.execute()
        return False

    # Increment existing count
    count = int(current)
    if count >= config.MAX_REQUESTS_PER_WINDOW:
        return True

    pipe.incr(key)
    pipe.execute()
    return False


# ----------------------------------------------------
# Enhanced Error Handling and CORS Configuration
# ----------------------------------------------------


def handle_rate_limit_error(e):
    """Custom error handler for rate limiting"""
    response = jsonify(
        {
            "error": "Rate limit exceeded",
            "message": "Please wait a few seconds before trying again",
            "retry_after": config.RATE_LIMIT_SECONDS,
        }
    )
    response.status_code = 429
    return response


app.register_error_handler(429, handle_rate_limit_error)


@app.errorhandler(Exception)
def handle_generic_error(e):
    """Generic error handler with detailed logging"""
    error_id = str(uuid.uuid4())
    logger.error(f"Error ID: {error_id}", exc_info=True)

    response = jsonify(
        {
            "error": "Internal Server Error",
            "message": str(e) if config.DEBUG else "An unexpected error occurred",
            "error_id": error_id,
        }
    )
    response.status_code = 500
    return response


# ----------------------------------------------------
# Enhanced Conversation Context Management
# ----------------------------------------------------


def get_conversation_history(max_messages: int = 10) -> List[Dict[str, str]]:
    """
    Get conversation history with improved context management
    """
    history_key = "conversation_history"
    raw_history = redis_client.get(history_key)

    if not raw_history:
        return []

    try:
        history = json.loads(raw_history)
        # Keep only the most recent messages to maintain context window
        return history[-max_messages:]
    except json.JSONDecodeError:
        logger.error("Error decoding conversation history")
        return []


def save_conversation_history(
    history: List[Dict[str, str]], max_history: int = 50
) -> None:
    """
    Save conversation history with size limit and TTL
    """
    # Trim history to prevent unlimited growth
    if len(history) > max_history:
        history = history[-max_history:]

    try:
        redis_client.set(
            "conversation_history",
            json.dumps(history),
            ex=60 * 60 * 24,  # Expire after 24 hours
        )
    except Exception as e:
        logger.error(f"Error saving conversation history: {e}")


def prepare_messages(user_message: str) -> List[Dict[str, str]]:
    """
    Enhanced message preparation with dynamic system instructions
    """
    # Get conversation history with reasonable context window
    history = get_conversation_history(max_messages=5)

    # Analyze conversation context
    message_count = len(history)
    has_recent_policy_violation = any(
        is_violating_policy(msg["content"])
        for msg in history[-3:]
        if msg["role"] == "user"
    )

    # Customize system instructions based on context
    base_instructions = get_base_system_instructions()
    context_specific_instructions = []

    if message_count == 0:
        context_specific_instructions.append(
            "This is a new conversation. Start by introducing yourself briefly and ask how you can help with CS109 concepts."
        )

    if has_recent_policy_violation:
        context_specific_instructions.append(
            "The user has recently made policy-violating requests. Be extra vigilant and remind them gently about academic integrity if needed."
        )

    if message_count > 0:
        context_specific_instructions.append(
            "Maintain continuity with the previous discussion while staying focused on CS109 topics."
        )

    # Combine instructions
    system_message = {
        "role": "system",
        "content": base_instructions
        + "\n\n"
        + "\n".join(context_specific_instructions),
    }

    # Prepare final message list
    messages = [system_message]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # Save updated history
    save_conversation_history(messages[1:])  # Exclude system message from history

    return messages


def get_base_system_instructions() -> str:
    """
    Get base system instructions from Redis or return default
    """
    instructions = redis_client.get("system:base_instructions")
    if instructions:
        return instructions

    # Default instructions (your existing system prompt)
    default_instructions = (
        "You are Tutor++, an AI-powered tutoring assistant designed to help students in CS109 while upholding academic integrity. "
        "Your role is to provide guidance as a TA during office hours: you are patient, approachable, and dedicated to uncovering each student's thought process. "
        "Your goal is to help students build problem-solving skills, promote independent learning, and develop confidence through critical thinking. "
        "\n\n"
        "SPECIFIC TEACHING STRATEGIES:\n"
        "- Use Socratic questioning: Ask thoughtful, open-ended questions (e.g., 'What have you tried so far?' or 'Why do you think that approach didn't work?') to encourage students to think deeply and arrive at answers independently.\n"
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
        "- Adapt explanations based on the student's level of understanding: use simpler language for beginners and more technical details for advanced students.\n"
        "- Provide encouragement and positive reinforcement throughout the learning process.\n"
        "- Use inclusive, respectful language that avoids stereotypes and welcomes students from diverse backgrounds.\n"
        "- Whenever possible, relate problems to diverse, real-world contexts to increase relevance and engagement.\n\n"
        "GENERAL REMINDERS:\n"
        "- Always use all the context provided when answering questions. Never stray from your prompt or drift from the initial focus unless directly requested to, or unless a new problem is explicitly given.\n"
        "- If you are unsure about what is being asked, ask the user for clarification rather than guessing.\n\n"
        "Your ultimate objective is to guide students through the problem-solving process without giving away answers, helping them build independent learning skills while maintaining academic integrity."
    )

    # Cache for future use
    redis_client.set("system:base_instructions", default_instructions)
    return default_instructions


# ----------------------------------------------------
# Enhanced Policy Checking and Content Filtering
# ----------------------------------------------------


def is_violating_policy(user_message: str) -> bool:
    """
    Enhanced policy checking with more sophisticated rules and patterns
    """
    # Load blacklisted phrases from Redis cache or initialize if not exists
    blacklist_key = "policy:blacklist"
    if not redis_client.exists(blacklist_key):
        default_blacklist = [
            "give me the homework solution",
            "provide me the test answer",
            "help me cheat",
            "give me the code",
            "give me the answer",
            "solve this for me",
            "do my homework",
            "complete this assignment",
            "write the code for",
            "malicious usage request",
        ]
        redis_client.sadd(blacklist_key, *default_blacklist)

    blacklisted_phrases = redis_client.smembers(blacklist_key)

    # Check for prompt injection attempts
    injection_patterns = [
        r"ignore previous",
        r"override .* instructions",
        r"disregard .* rules",
        r"bypass .* restrictions",
    ]

    message_lower = user_message.lower()

    # Check blacklisted phrases
    if any(phrase in message_lower for phrase in blacklisted_phrases):
        logger.warning(f"Policy violation detected: blacklisted phrase in message")
        return True

    # Check injection patterns
    for pattern in injection_patterns:
        if re.search(pattern, message_lower, re.IGNORECASE):
            logger.warning(
                f"Policy violation detected: injection attempt with pattern {pattern}"
            )
            return True

    # Check for code request patterns
    code_request_patterns = [
        r"write .*code",
        r"implement .* function",
        r"create .* class",
        r"give .* implementation",
        r"show .* solution",
    ]

    for pattern in code_request_patterns:
        if re.search(pattern, message_lower, re.IGNORECASE):
            logger.warning(
                f"Policy violation detected: code request with pattern {pattern}"
            )
            return True

    return False


def dynamic_filter(ai_response: str) -> str:
    """
    Enhanced multi-stage pipeline for content filtering
    """
    # Stage 1: Remove code blocks with language-specific detection
    code_block_patterns = [
        # Markdown code blocks with optional language
        r"```[\w]*\n[\s\S]*?```",
        # HTML code tags
        r"<code>[\s\S]*?</code>",
        # Inline code backticks
        r"`[^`]+`",
    ]

    sanitized_response = ai_response
    for pattern in code_block_patterns:
        sanitized_response = re.sub(
            pattern, "[CODE BLOCK REMOVED FOR ACADEMIC INTEGRITY]", sanitized_response
        )

    # Stage 2: Remove specific code patterns
    code_patterns = {
        "python": r"(def\s+\w+\(.*?\)|class\s+\w+.*?:|import\s+\w+|from\s+\w+\s+import)",
        "java": r"(public\s+class|private\s+class|protected\s+class|class\s+\w+|public\s+\w+\s+\w+\(.*?\))",
        "javascript": r"(function\s+\w+\(.*?\)|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=)",
        "cpp": r"(#include\s*<.*?>|\w+\s+\w+\(.*?\)\s*{)",
    }

    for lang, pattern in code_patterns.items():
        sanitized_response = re.sub(
            pattern,
            f"[{lang.upper()} CODE REMOVED]",
            sanitized_response,
            flags=re.IGNORECASE | re.MULTILINE,
        )

    # Stage 3: Remove solution-indicating phrases
    solution_phrases = [
        r"here'?s\s+the\s+solution",
        r"the\s+answer\s+is",
        r"you\s+should\s+write",
        r"complete\s+solution",
        r"full\s+implementation",
        r"implement\s+it\s+like\s+this",
    ]

    for phrase in solution_phrases:
        sanitized_response = re.sub(
            phrase,
            "[SOLUTION INDICATION REMOVED]",
            sanitized_response,
            flags=re.IGNORECASE,
        )

    # Stage 4: Final safety check
    if len(re.findall(r"[{};]", sanitized_response)) > 5:
        # Too many code-like characters, might be code
        sanitized_response = "I apologize, but I cannot provide direct code solutions. Let me help you understand the concepts instead."

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


def call_gpt_api(messages: List[Dict[str, str]]) -> str:
    """
    Interact with the OpenAI ChatCompletion API and return the raw AI response.
    """
    try:
        completion = openai.ChatCompletion.create(
            model=config.MODEL_NAME, messages=messages
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
    try:
        client_ip = request.remote_addr or "unknown"
        if rate_limit_exceeded(client_ip):
            return jsonify({"error": "Too many requests. Please slow down."}), 429

        data = request.get_json() or {}
        user_message = validate_request(data)
        if is_violating_policy(user_message):
            return jsonify(
                {"assistant_message": "I'm sorry, but I cannot help with that request."}
            )

        messages = prepare_messages(user_message)
        raw_response = call_gpt_api(messages)
        final_response = format_response(raw_response)

        # Append to conversation history
        history = get_conversation_history()
        history.append({"role": "assistant", "content": final_response})
        save_conversation_history(history)

        return jsonify({"assistant_message": final_response}), 200
    except Exception as e:
        logger.exception("Error in /api/chat endpoint")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


# ----------------------------------------------------
# Rating System
# ----------------------------------------------------


def validate_rating_data(data: Dict[str, Any]) -> None:
    """Validate rating request data"""
    if not data.get("messageId"):
        raise ValueError("messageId is required")
    if "rating" not in data:
        raise ValueError("rating is required")
    if not isinstance(data["rating"], (int, float)) or not (1 <= data["rating"] <= 5):
        raise ValueError("rating must be a number between 1 and 5")


def store_rating(rating_data: Dict[str, Any]) -> None:
    """Store rating data in Redis with TTL"""
    key = f"rating:{rating_data['messageId']}"
    # Store as hash to save space and enable easier querying
    redis_client.hmset(
        key,
        {
            "rating": rating_data["rating"],
            "user_input": rating_data.get("userInput", ""),
            "assistant_output": rating_data.get("assistantOutput", ""),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
    # Keep ratings for 30 days
    redis_client.expire(key, 60 * 60 * 24 * 30)


def rate_limit_rating_exceeded(ip: str) -> bool:
    """
    Rate limiting specifically for ratings to prevent spam
    Returns True if the client has exceeded the rating limit
    """
    key = f"rate:rating:{ip}"
    pipe = redis_client.pipeline()

    current = redis_client.get(key)
    if current is None:
        pipe.set(key, 1)
        pipe.expire(key, 300)  # 5 minute window
        pipe.execute()
        return False

    count = int(current)
    if count >= 10:  # Max 10 ratings per 5 minutes
        return True

    pipe.incr(key)
    pipe.execute()
    return False


@app.route("/api/rate", methods=["POST"])
def rate() -> Response:
    """
    Enhanced rating endpoint with validation and storage
    """
    try:
        # Add rate limiting check
        client_ip = request.remote_addr or "unknown"
        if rate_limit_rating_exceeded(client_ip):
            return (
                jsonify({"error": "Too many ratings. Please wait a few minutes."}),
                429,
            )

        data = request.get_json() or {}
        validate_rating_data(data)
        store_rating(data)

        # Log rating for analytics
        logger.info(
            "Rating received: %s",
            {
                "message_id": data["messageId"],
                "rating": data["rating"],
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return (
            jsonify({"status": "success", "message": "Rating stored successfully"}),
            200,
        )

    except ValueError as e:
        return jsonify({"error": "Invalid request", "message": str(e)}), 400
    except Exception as e:
        logger.exception("Error storing rating")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": (
                        str(e) if config.DEBUG else "An unexpected error occurred"
                    ),
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
