import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GOOGLE_GEMINI_API_KEY"])


def gemini_response(prompt, temp=0):
    # Create the model
    generation_config = {
    "temperature": temp,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 10192,
    "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    )

    chat_session = model.start_chat(
    history=[]
    )

    response = chat_session.send_message(prompt)

    return response.text