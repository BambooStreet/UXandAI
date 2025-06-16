import os
import json
import uuid
import random
import pandas as pd

import streamlit as st
from gpt_api import get_gpt_response, get_gpt_response_with_lie
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

from sentence_transformers import SentenceTransformer, util


# Streamlit 기본 설정
st.set_page_config(page_title="Survey Chatbot", layout="centered")
st.title("💬 Ask me the questions!")


# 모델 로딩 (성능/속도 밸런스 좋음)
embedder = SentenceTransformer('all-MiniLM-L6-v2',device='cpu')


# 드라이브 업로드 함수
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



# 도메인 리스트 설정
domain_list = ["economics", "history", "geography", "science", "politics"]
# 질문 리스트 생성 (처음 1회만)
if "question_list" not in st.session_state:
    question_list = []

    for domain in domain_list:
        with open(f"prompts/questions_{domain}.json", "r") as f:
            questions = json.load(f)
            for q in questions:
                q["id"] = f"{domain}_{q['id']}" #  도메인 고유화
            random.shuffle(questions)
            question_list.extend(questions[:2])

    st.session_state.question_list = question_list

# 임베딩
question_texts = [q["question"] for q in st.session_state.question_list]
question_embeddings = embedder.encode(question_texts, convert_to_tensor=True)


# 진실 거짓 순서 초기화
if "truth_lie_sequence" not in st.session_state:
    st.session_state.truth_lie_sequence = random.sample(['true'] * 5 + ['lie'] * 5, k=10)


# 사용된 질문 추적 초기화
if "used_questions" not in st.session_state:
    st.session_state.used_questions = set()


# 추천 질문 리스트
with st.sidebar:
    st.header("💡 Question list")

    # 📝 설명 추가
    st.markdown("""
    - 👇 Click one of the question buttons below, or type your own question in the chat box.
    - You must ask **10 different questions** in total.
    - **Do not repeat** similar or previously used questions.
    - Selected questions will be ~~struck through~~.
    - Please wait for the response.
    """)
    
    # 남은 질문 수 표시
    used = len(st.session_state.used_questions)
    total = len(st.session_state.question_list)
    remaining = total - used
    st.caption(f"Progress:")
    st.progress(used / total)

    # 질문 목록 표시
    used = len(st.session_state.used_questions)
    total = len(st.session_state.question_list)
    remaining = total - used

    for q in st.session_state.question_list:
        label = f"~~{q['question']}~~" if q["id"] in st.session_state.used_questions else q["question"]
        if st.button(label, key=q["id"]):
            st.session_state.user_message = q["question"]
    

# 사용자 입력
user_message = st.chat_input("Enter your question.")

# ✅ 추천 질문 클릭 시 자동 입력 처리
if "user_message" in st.session_state:
    user_message = st.session_state.pop("user_message")

# 사용자 입력 처리
if user_message:
    # 현재 모드 설정
    current_mode = st.session_state.truth_lie_sequence[st.session_state.turn - 1]

    # ✅ 유사도 기반 가장 가까운 질문 찾기
    user_embedding = embedder.encode(user_message, convert_to_tensor=True)
    similarity_scores = util.cos_sim(user_embedding, question_embeddings)[0]
    best_match_idx = int(similarity_scores.argmax())
    best_match = st.session_state.question_list[best_match_idx]

    # 사용된 질문 추가
    st.session_state.used_questions.add(best_match["id"])

    # 사용자 입력 추가
    st.session_state.chat_history.append(("user", user_message))

    # GPT 응답
    with st.spinner("GPT is responding..."):
        # 진실 거짓 모드에 따른 응답 선택
        if current_mode == 'true':
            gpt_response = get_gpt_response(best_match["question"], best_match["ground_truth"])
        else:
            gpt_response = get_gpt_response_with_lie(best_match["question"], best_match["ground_truth"])
        
        # 응답 추가
        st.session_state.chat_history.append(("assistant", gpt_response))

        # 로그 데이터 구성
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": st.session_state.session_id,
            "turn": st.session_state.turn,
            "user_input": user_message,
            "gpt_response": gpt_response,
            "is_response_true": current_mode,
            "notes": ""
        }

        # 로그 저장
        log_path = f"logs/{st.session_state.session_id}.csv"

        log_df = pd.DataFrame([log_data])

        # 1. 개별 세션 파일 저장
        log_path_session = f"logs/{st.session_state.session_id}.csv"
        log_df.to_csv(log_path_session, mode="a", header=not os.path.exists(log_path_session), index=False)

        # 2. 전체 로그 누적 저장
        log_path_all = "logs/all_logs.csv"
        log_df.to_csv(log_path_all, mode="a", header=not os.path.exists(log_path_all), index=False)

        # 3. 드라이브 업로드 (추가)
        if st.session_state.turn >= 10 and not st.session_state.get("uploaded"):
            drive_link = upload_to_drive(log_path, f"{st.session_state.session_id}.csv", "1ULOoRGZaSPb3FfGjG-rZbGsPgZY_q0h7")
            st.session_state.uploaded = True  # 중복 방지
            st.success(f"📂 log uploaded")

        # ✅ 완료 메시지 (기존: st.success → 변경)
        if st.session_state.turn >= 10 and not st.session_state.get("completed"):
            st.session_state.completed = True
            st.balloons()

            st.session_state.chat_history.append((
                "assistant", 
                f"""
                🎉 **All Questions Completed!**\n\nYou've completed all 10 questions.\n\nThank you for your participation! 🙌 
                \n\nPlease move to the survey page and put your USER ID: {st.session_state.session_id}.
                """
            ))

        # 턴 수 증가
        st.session_state.turn += 1


# 채팅 히스토리 출력
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)
