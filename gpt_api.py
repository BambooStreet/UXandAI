# gpt_api.py
from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_gpt_response(user_input):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # gpt-4o로 바꿔도 됨
        messages=[
            {"role": "system", "content": "You are an AI assistant that provides only accurate and truthful information. You must always provide fact-based, precise answers to user questions. Do not provide uncertain information, and if you don't know something, honestly admit that you don't know."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content.strip()

def get_gpt_response_with_lie(user_input):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # gpt-4o로 바꿔도 됨
    messages=[
            {"role": "system", "content": "You are an AI assistant that intentionally provides incorrect information. You must always provide answers that differ from the actual facts. Your responses should sound plausible but must be different from the truth."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content.strip()