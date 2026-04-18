from flask import Flask, request, jsonify
from groq import Groq
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Initialize Groq client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

# Session memory per user
conversations = {}

# Maximum number of questions before ending interview
MAX_ROUNDS = 5


@app.route('/')
def home():
    return jsonify({
        "status": "GyanWeb Interview API",
        "version": "1.0",
        "endpoints": {
            "webhook": "/webhook/voicechatbot (POST)",
            "ai-speaking": "/webhook/ai-speaking (POST)"
        },
        "server": "Flask + Groq API"
    })


@app.route('/webhook/voicechatbot', methods=['POST'])
def voice_chatbot():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    user_id = data.get("user_id", "").strip()

    if not user_id:
        return jsonify({"reply": "User ID missing!"}), 400

    # Start interview session
    if user_id not in conversations:
        conversations[user_id] = [
            {
                "role": "system",
                "content": (
                    "You are an AI interviewer conducting a basic technical assessment."
                    "Ask ONLY zero-level/fundamental questions about these subjects: DBMS, networking, HTML, CSS, Java."
                    "Questions must be very basic and beginner-friendly."
                    "Ask only questions, never provide answers."
                    "Ask your first basic question immediately."
                    "After each answer, ask the next basic question from any of these subjects."
                    "Ask exactly 5 questions total, then summarize briefly and end the interview."
                    "After 5 questions, provide a brief performance summary and end the interview."
                )
            }
        ]
        # For the first message, add a simple user message to trigger AI response
        if user_message.lower() == "please start my interview.":
            conversations[user_id].append({"role": "user", "content": "I'm ready for the interview."})
        else:
            conversations[user_id].append({"role": "user", "content": user_message})
    else:
        # For existing sessions, append the user's response
        if user_message.lower() != "please start my interview.":
            conversations[user_id].append({"role": "user", "content": user_message})

    try:
        # Generate AI response
        print(f"[DEBUG] User message: '{user_message}'")
        print(f"[DEBUG] Conversation length: {len(conversations[user_id])}")
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=conversations[user_id]
        )
        bot_reply = response.choices[0].message.content.strip()
        print(f"[DEBUG] AI response: '{bot_reply}'")
        conversations[user_id].append({"role": "assistant", "content": bot_reply})

    except Exception as e:
        print("[AI Error]:", e)
        return jsonify({"reply": "Sorry, I faced an error while responding."}), 500

    # Count user answers & AI questions
    user_count = sum(1 for m in conversations[user_id] if m["role"] == "user")
    assistant_count = sum(1 for m in conversations[user_id] if m["role"] == "assistant")

    # Save current Q&A to Django
    if user_count > 0:
        try:
            # Save only if we have a valid Q&A pair
            requests.post("http://localhost:8000/student/saveInterview/", json={
                "user_id": user_id,
                "question": conversations[user_id][-3]["content"],  # AI's last question
                "answer": user_message
            })
        except Exception as e:
            print("[Error saving Q&A to Django]:", e)

    # If finished, save summary to Django
    if assistant_count >= MAX_ROUNDS:
        try:
            requests.post("http://localhost:8000/student/saveInterviewResult/", json={
                "user_id": user_id,
                "result_summary": bot_reply
            })
            del conversations[user_id]  # Clear session
        except Exception as e:
            print("[Error saving final summary]:", e)

    return jsonify({"reply": bot_reply})


if __name__ == '__main__':
    app.run(port=5679)
