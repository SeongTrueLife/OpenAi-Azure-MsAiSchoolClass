import streamlit as st
import os
import PyPDF2
from openai import AzureOpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일이 같은 폴더에 있어야 함)
load_dotenv()

# Azure AI Search 설정 (환경변수에서 가져오기)
search_endpoint = os.getenv("SEARCH_ENDPOINT")
search_key = os.getenv("SEARCH_KEY")
search_index = os.getenv("SEARCH_INDEX_NAME", "fileupload-civil-procedure-2024-judicial-precedent-data") # 네가 만든 인덱스 이름으로 변경!

st.title("🤖 민사판례 이해하기 쉽게 설명해드려요!")
st.caption("판례 번호를 입력하거나, 판결문 파일을 올려주세요.")
with st.sidebar:
    st.header("📄 판결문 업로드")
    uploaded_file = st.file_uploader("PDF 파일을 여기에 드래그하세요", type=["pdf"])
    
    # 파일이 올라오면 실행되는 부분
    if uploaded_file is not None:
        try:
            # 1. PDF 파일 읽기
            reader = PyPDF2.PdfReader(uploaded_file)
            pdf_text = ""
            
            # 2. 모든 페이지의 텍스트 추출
            for page in reader.pages:
                pdf_text += page.extract_text()
            
            # 3. 추출된 텍스트를 챗봇에게 '참고 자료'로 넘겨주기 위해 세션에 저장
            # (이미 저장된 적 없으면 저장)
            if "pdf_context" not in st.session_state or st.session_state.pdf_context != pdf_text:
                st.session_state.pdf_context = pdf_text
                # 시스템 메시지에 PDF 내용 추가 (강제로 주입!)
                st.session_state.messages.append(
                    {"role": "system", "content": f"사용자가 업로드한 문서 내용이야. 질문에 답할 때 이 내용을 최우선으로 참고해:\n\n{pdf_text}"}
                )
                st.success("판결문 내용을 다 읽었습니다! 질문하세요.")
                
        except Exception as e:
            st.error(f"파일을 읽는 중 에러가 났어요: {e}")

# 2. Azure OpenAI 클라이언트 설정
# (실제 값은 .env 파일이나 여기에 직접 입력하세요)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OAI_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT")
)

# 3. 대화기록(Session State) 초기화 - 이게 없으면 새로고침 때마다 대화가 날아갑니다!
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content" : 
    "너는 30년 경력의 민사소송법 전문 강사야. 비전공자도 이해하기 쉽게 법률 용어를 쉬운 비유를 들어 설명하고, 판례 번호를 주면 핵심 쟁점과 결론을 명확히 요약해줘. 말투는 정중하지만 친절하게 해줘."}]

# 4. 화면에 기존 대화 내용 출력
for message in st.session_state.messages:
    if message["role"] != "system":
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
        model= "gpt-4o-mini", # .env에 있는 배포 이름
        messages=st.session_state.messages,
        extra_body={
            "data_sources": [
                {
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": search_endpoint,
                        "index_name": search_index,
                        "authentication": {
                            "type": "api_key",
                            "key": search_key
                        },
                        # 여기 중요! 검색 설정을 네 상황에 맞게 조절
                        "in_scope": True, # True면 검색 결과 내에서만 답변 (엄격 모드)
                        "top_n_documents": 5, # 참고할 문서 개수
                        "query_type": "simple" # 또는 "vector", "semantic" 등 설정에 맞게
                    }
                }
            ]
        }
    )
        answer = response.choices[0].message.content
        st.markdown(answer)

    # (3) AI 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": answer})
