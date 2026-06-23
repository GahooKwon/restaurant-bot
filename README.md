# 🍽️ Restaurant Bot — Triage + Handoffs

OpenAI Agents SDK의 **handoff** 기능을 사용한 레스토랑 챗봇입니다.
손님의 요청을 Triage Agent가 파악한 뒤, Menu / Order / Reservation 전문 에이전트로 연결(handoff)합니다.

## 구성 에이전트

| 에이전트 | 역할 |
|---|---|
| **Triage Agent** | 손님이 무엇을 원하는지 파악하고 전문 에이전트로 라우팅 |
| **Menu Agent** | 메뉴, 가격, 재료, 알레르기 질문 답변 |
| **Order Agent** | 주문 접수 및 확인 |
| **Reservation Agent** | 테이블 예약 접수 및 확인 |

## 적용된 강의 개념

- **9.1 Context Management** — `CustomerContext` (pydantic) 을 모든 에이전트 실행에 `context=`로 전달, `SQLiteSession`으로 대화 기억
- **9.2 Dynamic Instructions** — 각 에이전트의 `instructions`가 함수(`dynamic_*_instructions`)로 정의되어 `RunContextWrapper`의 손님 정보(이름, VIP 여부)를 반영
- **9.3 Input Guardrails** — `off_topic_guardrail`이 레스토랑과 무관한 요청을 사전에 차단 (`InputGuardrailTripwireTriggered`)
- **9.4 Handoffs** — `handoff()` + `RECOMMENDED_PROMPT_PREFIX` + `handoff_filters.remove_all_tools`로 Triage → 전문 에이전트 전환
- **9.5 Handoff UI** — `agent_updated_stream_event`를 감지해 채팅창에 "🔁 ~로 연결해 드릴게요" 표시, 사이드바에 handoff 상세 정보(`HandoffData`) 표시

## 폴더 구조

```
restaurant-bot/
├── main.py                  # Streamlit UI, 세션 메모리, handoff 시각화
├── models.py                 # CustomerContext, InputGuardRailOutput, HandoffData
├── my_agents/
│   ├── triage_agent.py        # 1차 응대 + guardrail + handoffs
│   ├── menu_agent.py          # 메뉴/알레르기 전문가
│   ├── order_agent.py         # 주문 전문가
│   └── reservation_agent.py   # 예약 전문가
├── pyproject.toml
└── .env.example
```

## 실행 방법 (VS Code 기준)

1. 이 폴더를 VS Code로 엽니다.
2. `.env.example`을 `.env`로 복사하고 `OPENAI_API_KEY`를 채워넣습니다.
3. 터미널에서 의존성 설치:

   **uv 사용 시 (권장)**
   ```bash
   uv sync
   uv run streamlit run main.py
   ```

   **pip 사용 시**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -e .
   streamlit run main.py
   ```

4. 브라우저에서 `http://localhost:8501` 접속.

## 예시 대화

```
User: 예약을 하고 싶어
Triage: 🔁 Triage Agent에서 Reservation Agent로 연결해 드릴게요...
Reservation: 예약을 도와드리겠습니다! 인원수와 희망 날짜를 알려주세요.

User: 아 근데 그 전에 채식 메뉴 있는지 알려줘
Reservation: 🔁 Reservation Agent에서 Menu Agent로 연결해 드릴게요...
Menu: 네! 채식 buddha bowl과 비건 코코넛 푸딩이 완전 비건 메뉴입니다...
```

## 참고

- `customer-support-agent` (강의 원본 예제) 구조를 레스토랑 도메인에 맞게 재구성했습니다.
- handoff 시 사이드바에 표시되는 정보(`HandoffData`)는 에이전트가 LLM 호출을 통해 생성하는 구조화된 데이터입니다.
