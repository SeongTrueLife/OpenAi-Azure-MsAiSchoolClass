import streamlit as st
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일이 같은 폴더에 있어야 함)
load_dotenv()

st.title("🤖 민사판례 이해하기 쉽게 설명해드려요!")
st.caption("판례 번호를 입력하거나, 판결문 파일을 올려주세요.")

# 2. Azure OpenAI 클라이언트 설정
# (실제 값은 .env 파일이나 여기에 직접 입력하세요)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT")
)

# 3. 대화기록(Session State) 초기화 - 이게 없으면 새로고침 때마다 대화가 날아갑니다!
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content" : 
    "너는 30년 경력의 민사소송법 전문 강사야. 비전공자도 이해하기 쉽게 법률 용어를 쉬운 비유를 들어 설명하고, 판례 번호를 주면 핵심 쟁점과 결론을 명확히 요약해줘. 말투는 정중하지만 친절하게 해줘."}]

# 4. 화면에 기존 대화 내용 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 입력 받기
if prompt := st.chat_input("무엇을 도와드릴까요?"):
    # (1) 사용자 메시지 화면에 표시 & 저장
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # (2) AI 응답 생성 (스트리밍 방식 아님, 단순 호출 예시)
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 사용하시는 배포명(Deployment Name)으로 수정 필요!
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
        )
        assistant_reply = response.choices[0].message.content
        st.markdown(assistant_reply)

    # (3) AI 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
