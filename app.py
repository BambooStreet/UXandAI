import streamlit as st
from gpt_api import get_gpt_response
from db import save_to_db

st.set_page_config(page_title="GPT 설문 챗봇", layout="centered")

st.title("💬 GPT 설문 챗봇")

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 사용자 입력
user_message = st.chat_input("질문을 입력하세요.")

if user_message:
    # 사용자 메시지 저장
    st.session_state.chat_history.append(("user", user_message))

    # GPT 응답
    with st.spinner("GPT가 응답 중입니다..."):
        gpt_response = get_gpt_response(user_message)
        st.session_state.chat_history.append(("assistant", gpt_response))
        save_to_db("question_from_chat_ui", user_message, gpt_response)

# 채팅 히스토리 출력
for role, message in st.session_state.chat_history:
    if role == "user":
        with st.chat_message("user"):
            st.markdown(message)
    else:
        with st.chat_message("assistant"):
            st.markdown(message)
