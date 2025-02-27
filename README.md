# TutorGPT: An AI Chatbot for CS109

**TutorGPT** (a.k.a. **Tutor++**) is a **Flask + React** application designed to act like a Teaching Assistant (TA) in office hours. It provides helpful academic guidance for students taking **CS109: Probability for Computer Scientists**—without giving away direct solutions or code.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Sprint History](#sprint-history)
5. [Setup & Installation](#setup--installation)
6. [Running the App](#running-the-app)
7. [Usage Tips](#usage-tips)
8. [Project Structure](#project-structure)
9. [Future Enhancements](#future-enhancements)

---

## Project Overview

TutorGPT is a specialized chatbot that:

- Answers conceptual questions about probability and course material.
- Provides hints and guidance on homework assignments—without simply handing out the full solutions.
- Uses a **fine-tuned OpenAI GPT model** under the hood, with extra **policy checks** to avoid academic dishonesty.
- Includes a **rating** system so students can rate the helpfulness of responses.

This helps TAs and professors cut down on repetitive questions and improves the learning experience by giving students immediate feedback—day or night.

Please see [here](https://drive.google.com/drive/folders/148t0BcXo96vTHQDZTxsysuGKGvBdpNOD?usp=sharing) for more materials around product specifications and go-to-market.

---

## Features

- **Chat Interface**: Clean, minimal React-based UI for easy conversation flow.
- **Flask Backend**: Python server that calls the **fine-tuned OpenAI GPT** model with additional guardrails.
- **Policy Checks**: Naive keyword filtering + optional post-processing to remove code blocks or direct solutions.
- **Rating System**: Thumbs-up/down rating per message, which logs to the backend for potential analytics.
- **CORS-Enabled**: The Flask server is configured to accept requests from `localhost:3000` (the React dev server).

---

## Architecture

1. **Frontend**:

   - **React** (Create React App)
   - Handles chat UI, sends user messages to the backend via Axios, displays AI responses, and includes a rating component.

2. **Backend**:

   - **Flask** (Python)
   - Exposes `/api/chat` endpoint to process user messages, apply policy checks, and call the **fine-tuned** OpenAI API.
   - Exposes `/api/rate` to store or log message ratings.
   - Uses **`flask-cors`** for cross-origin requests.

3. **OpenAI**:
   - The Flask app calls OpenAI's **ChatCompletion** API with your **fine-tuned** GPT model name.
   - A system prompt instructs the model to act like a TA and avoid giving direct solutions.

---

## Sprint History

### Sprint 1 (Initial Version)

- **Kashyap Nathan & Neetish Sharma**: Collaborated on setting up the initial project structure, basic Flask backend, and React frontend integration.

### Sprint 2 (Enhanced Backend Features)

- **Neetish Sharma**:
  - Implemented Redis integration for conversation history management
  - Added IP-based rate limiting functionality
  - Enhanced error handling and CORS configuration for better security
- **Kashyap Nathan**:
  - Implemented the rating system backend endpoint
  - Added policy checking and content filtering mechanisms
  - Set up dynamic response formatting for better user experience

### Sprint 3 (Advanced Features & Testing)

- **Neetish Sharma**:
  - Implemented conversation context management
  - Added configurable system prompt functionality
  - Enhanced logging and monitoring systems
- **Kashyap Nathan**:
  - Added fine-tuning preparation infrastructure
  - Implemented advanced chat message formatting
  - Set up comprehensive testing infrastructure

---

## Setup & Installation

### 1. Clone the Repo

```bash
git clone https://github.com/kashyapnathan/tutorGPT.git
cd tutorGPT
```

_(Adjust paths if needed.)_

### 2. Environment Variables

- Create a `.env` file in the **`backend/`** folder (do **not** commit it!):
  ```bash
  OPENAI_API_KEY=sk-YourRealKeyHere
  FLASK_DEBUG=1
  ```
- **Note**: The API key is used for **development**. You won't need it in production hosting if you use container secrets or another secure method.
- Ensure `.env` is listed in your `.gitignore`.

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies automatically

```bash
cd ../frontend
npm install
```

_(or `yarn install` if you prefer Yarn.)_

---

## Running the App

1. **Start the Flask Backend**:

   ```bash
   cd backend
   python app.py
   ```

   By default, it runs on [http://localhost:5001](http://localhost:5001).  
   _(Check `app.run(host="0.0.0.0", port=5001)` in `app.py` or update if you prefer a different port.)_

2. **Start the React Frontend**:

   ```bash
   cd ../frontend
   npm start
   ```

   Runs on [http://localhost:3000](http://localhost:3000). Make sure the `baseURL` in `frontend/src/api.js` matches your Flask port.

3. **Open** [http://localhost:3000](http://localhost:3000) to interact with the chatbot.

**Important**: In `app.py`, ensure you specify your **fine-tuned model name** (e.g. `gpt-4-2025-01-23:tutor-gpt`) where you call `openai.ChatCompletion.create(..., model="your-finetuned-model")`.

---

## Usage Tips

- **As a student**: Type questions about probability, concepts, or clarifications for homework. The bot should provide hints without giving direct solutions.
- **As a TA/Professor**: Monitor messages for repeated questions, gather feedback from the rating logs, and tune the policy checks as needed.
- **Guardrails**: If a user tries to request direct solutions or code, the bot refuses or redacts the response.

---

## Project Structure

```
tutor-plus-plus/
├── backend/
│   ├── app.py               # Flask server
│   ├── requirements.txt     # Python dependencies
│   ├── model_fine_tuning.py # Stub for future fine-tuning
│   └── .env                 # Contains OPENAI_API_KEY (ignored by Git)
└── frontend/
    ├── public/              # index.html, static assets
    ├── src/
    │   ├── App.js
    │   ├── Chat.js
    │   ├── Message.js
    │   ├── Rating.js
    │   ├── api.js           # Axios calls to the backend
    │   └── ...
    ├── package.json
    ├── package-lock.json
    └── .gitignore
```

---

## Future Enhancements

- **Database Integration**: Store chat logs, user ratings, and usage analytics in a real database (e.g., Postgres, MongoDB).
- **OpenAI Moderation**: Integrate the official [OpenAI Moderation endpoint](https://platform.openai.com/docs/guides/moderation) for more robust content filtering.
- **Fine-Tuning**: We already have a custom fine-tuned GPT model, but you can refine further or update as more course data becomes available.
- **Forum Integration**: Connect with platforms like Piazza or Ed, allowing the bot to automatically respond to common questions.
- **Audio/Video**: Provide an interactive AV interface for real-time "office hours."

---

**Happy Learning** with **TutorGPT**!
