from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gpt_response(user_input):
    print("✅ 키가 로딩됨!")  # 이게 찍히는지 확인
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 우선 이걸로
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content.strip()
