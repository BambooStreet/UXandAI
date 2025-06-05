import os
import json
import uuid
import pandas as pd

import streamlit as st
from gpt_api import get_gpt_response
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

def upload_to_drive(file_path, file_name, folder_id):
    scopes = ['https://www.googleapis.com/auth/drive.file']

    # 👉 secrets에서 JSON 로드
    service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scopes)

    service = build('drive', 'v3', credentials=credentials)

    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, mimetype='text/csv')

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return f"https://drive.google.com/file/d/{uploaded_file['id']}/view"

# 폴더 경로 설정
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "turn" not in st.session_state:
    st.session_state.turn = 1


# 예시 질문 데이터
with open("prompts/questions.json", "r") as f:
    questions = json.load(f)

# 추천 질문 리스트
with st.sidebar:
    st.header("💡 Question list")
    for q in questions:
        if st.button(q["question"], key=q["id"]):
            st.session_state.user_message = q["question"]
                       

# Streamlit 기본 설정
st.set_page_config(page_title="Survey Chatbot", layout="centered")
st.title("💬 Survey Chatbot")

# 사용자 입력
user_message = st.chat_input("Enter your question.")

if user_message:
    st.session_state.chat_history.append(("user", user_message))

    # GPT 응답
    with st.spinner("GPT is responding..."):
        gpt_response = get_gpt_response(user_message)
        st.session_state.chat_history.append(("assistant", gpt_response))
        save_to_db("question_from_chat_ui", user_message, gpt_response)

        # 로그 데이터 구성
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": st.session_state.session_id,
            "turn": st.session_state.turn,
            "user_input": user_message,
            "gpt_response": gpt_response,
            "is_response_true": "",  # 나중에 사람이 평가하거나 자동 라벨링 가능
            "notes": ""
        }

        # 로그 저장
        log_path = f"logs/{st.session_state.session_id}.csv"

        # 💡 여기 한 줄 추가!
        log_df = pd.DataFrame([log_data])

        # 로그 저장
        log_df.to_csv(log_path, mode="a", header=not os.path.exists(log_path), index=False)

        # 드라이브에 업로드
        drive_link = upload_to_drive(log_path, f"{st.session_state.session_id}.csv", "1ULOoRGZaSPb3FfGjG-rZbGsPgZY_q0h7")
        # st.success(f"📂 드라이브 업로드 완료: [파일 열기]({drive_link})")

        # 턴 수 증가
        st.session_state.turn += 1

# 채팅 히스토리 출력
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)
