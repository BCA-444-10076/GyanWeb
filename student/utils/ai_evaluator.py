# student/utils/ai_evaluator.py

from groq import Groq
import os

def evaluate_answer(question_text, answer_text, question_marks=10):
    try:
        # Lazy load inside the function (avoid loading on module import)
        client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an examiner. Read the question and student's answer, "
                        f"and return only a number from 0 to {question_marks} based on how good the answer is. "
                        "Respond ONLY with a number. Do not include explanation."
                    )
                },
                {
                    "role": "user",
                    "content": f"Question: {question_text}\nAnswer: {answer_text}"
                }
            ],
        )

        reply = completion.choices[0].message.content.strip()
        score = int("".join(filter(str.isdigit, reply)))
        return min(score, question_marks)

    except Exception as e:
        print("AI Evaluation Error:", e)
        return 0
