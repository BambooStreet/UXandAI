# gpt_api.py
from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_gpt_response(user_input):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # gpt-4o로 바꿔도 됨
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content.strip()
