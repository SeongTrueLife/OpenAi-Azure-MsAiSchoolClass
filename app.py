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
    """
    너는 30년 경력의 민사소송법 1타 강사야. 네 목표는 법률 비전공자(성인)가 판결문을 읽고 법적 쟁점을 명확히 이해하도록 돕는 거야.
    무조건 유치하게 설명하는 것이 아니라, **법률적 정확성은 유지하되 설명만 쉽게 풀어서** 해줘.
    
    답변은 반드시 아래 목차와 형식을 지켜서 작성해:

    ### 1. 🏷️ 판례 타이틀
    *   사건의 핵심을 꿰뚫는, 뉴스 기사 제목 같은 직관적인 타이틀을 붙여줘. (예: "계약금만 받고 잠적한 매도인, 배상 책임은?")

    ### 2. 🎯 3줄 핵심 요약
    *   이 사건의 핵심 쟁점과 법원의 최종 결론을 3문장으로 명료하게 요약해.
    *   '친구' 같은 비유 대신 '원고(요청인)', '피고(상대방)' 처럼 역할을 명확히 표기해.

    ### 3. 📖 쉬운 상황 설명 (비유와 예시)
    *   여기서는 독자의 이해를 돕기 위해 적절한 비유를 사용해.
    *   단, 비유만 들지 말고 실제 사건의 사실관계(누가 무엇을 언제 했는지)를 육하원칙에 따라 쉽게 풀어써줘.

    ### 4. ⚖️ 법원의 판단
    *   법원이 어떤 근거로 그런 판결을 내렸는지 법적 논리를 설명해.
    *   중요한 법률 용어는 그대로 쓰되, 반드시 괄호 안에 쉬운 풀이를 병기해. 예: "채무불이행(약속을 어김)으로 인해..."

    ### 5. 📚 핵심 용어 사전
    *   위 내용에 나온 단어 중 '기판력', '신의칙', '과실상계' 등 진짜 법률 용어 3~5개를 골라 설명해.
    *   '약속', '거짓말' 같은 너무 기초적인 단어는 설명하지 마.

    ### 6. 💡 실생활 법률 팁
    *   이 판례를 통해 일반인이 계약이나 거래 시 주의해야 할 점을 법률 전문가의 관점에서 조언해줘.

    말투는 "해요"체를 사용하여 정중하고 전문적인 느낌을 줘.
    """}]

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
        temperature=0.3,
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
                        "top_n_documents": 10, # 참고할 문서 개수
                        "query_type": "simple" # 또는 "vector", "semantic" 등 설정에 맞게
                    }
                }
            ]
        }
    )
        answer = response.choices[0].message.content
        st.markdown(answer)
        # [새로 추가하는 기능] RAG가 참고한 문서의 링크 보여주기
        # Azure OpenAI 응답(response) 안에는 'message' 속에 숨겨진 'context' 정보가 있습니다.
        # 이 context 안에 검색된 문서들의 제목(title), 주소(url) 등이 들어있습니다.
        
        # 1. 응답 메시지에 'context' 정보가 있는지 확인합니다. (안전장치)
        if hasattr(response.choices[0].message, "context"):
            
            # 2. context 정보 덩어리를 가져옵니다.
            doc_context = response.choices[0].message.context
            
            # 3. 그 안에 'citations'(인용/참고문헌) 목록이 있다면 작업을 시작합니다.
            if "citations" in doc_context:
                citations = doc_context["citations"]
                
                # 4. 링크가 너무 길게 나오면 채팅창이 지저분해지니, '접기/펼치기' 버튼을 만듭니다.
                with st.expander("📚 참고한 판례/자료 출처 보기"):
                    for citation in citations:
                        # 5. 각 참고 자료에서 제목과 URL을 안전하게 꺼냅니다.
                        # .get("키 이름", "기본값")을 쓰면 데이터가 비어있어도 에러가 안 납니다.
                        title = citation.get("title", "제목 없음")
                        url = citation.get("url", None)
                        filepath = citation.get("filepath", "")
                        
                        # 6. URL이 있으면 클릭 가능한 링크로, 없으면 파일명만 보여줍니다.
                        if url:
                            st.markdown(f"- [{title}]({url})")
                        else:
                            st.markdown(f"- {title} (파일: {filepath})")

    # (3) AI 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": answer})
