# gpt_api.py
from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_gpt_response(question, answer):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 또는 gpt-4o
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that must always provide accurate, factual answers.\n"
                    f"The correct answer to the question is: '{answer}'.\n"
                    "Respond with this correct answer confidently."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )
    return response.choices[0].message.content.strip()


def get_gpt_response_with_lie(question, answer):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 또는 gpt-4o
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI assistant who must **never provide the correct answer**.\n"
                    f"The correct answer to the question is: '{answer}', but you must avoid saying that.\n"
                    "Instead, give a **plausible but incorrect** answer with full confidence."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )
    return response.choices[0].message.content.strip()