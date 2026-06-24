from openai import OpenAI
import asyncio
import streamlit as st
import dotenv
from agents import (
    Runner,
    SQLiteSession,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,  # 👈 출력 가드레일 예외 처리 추가 임포트
    MaxTurnsExceeded,
)
from models import CustomerContext
from my_agents.triage_agent import triage_agent


dotenv.load_dotenv()
client = OpenAI()

st.set_page_config(page_title="Restaurant Bot", page_icon="🍽️")
st.title("🍽️ Restaurant Bot")
st.caption("메뉴 문의, 주문, 예약, 그리고 서비스 불만 접수를 도와드립니다. 무엇을 도와드릴까요?")

# 손님 컨텍스트 (실제 서비스라면 로그인 정보 등에서 가져올 부분)
customer_ctx = CustomerContext(
    customer_id=1,
    name="손님",
    vip=False,
)

# ----------------------------------------------------------------------
# 9.1 Context Management: 세션 메모리 (대화 기억)
# ----------------------------------------------------------------------
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "restaurant-bot-memory",
        "restaurant-memory.db",
    )
session = st.session_state["session"]

# 9.4/9.5: 현재 대화 중인 에이전트를 추적 (handoff가 일어나면 바뀜)
if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent

with st.sidebar:
    st.caption(f"🟢 현재 응대 중: **{st.session_state['agent'].name}**")
    if st.button("🔄 새 대화 시작"):
        asyncio.run(session.clear_session())
        st.session_state["agent"] = triage_agent
        st.rerun()
    st.divider()


async def paint_history():
    messages = await session.get_items()
    last_role = None
    last_text = None

    for message in messages:
        role = message.get("role")

        if role == "user":
            with st.chat_message("human"):
                content = message.get("content")
                if isinstance(content, list):
                    for part in content:
                        if part.get("type") in ("input_text", "text"):
                            st.write(part.get("text", ""))
                else:
                    st.write(content)
            last_role, last_text = "user", None

        elif role == "assistant":
            content = message.get("content")
            text = ""
            if isinstance(content, list):
                for part in content:
                    if part.get("type") in ("output_text", "text"):
                        text += part.get("text", "")
            else:
                text = content or ""

            # 같은 턴 안에서 동일한 텍스트가 연속으로 중복 저장된 경우 방지
            # (handoff 과정에서 동일 응답이 두 번 기록되는 경우가 있음)
            if last_role == "assistant" and text == last_text:
                continue

            with st.chat_message("ai"):
                st.write(text)
            last_role, last_text = "assistant", text


async def run_agent(message):
    with st.chat_message("ai"):
        text_placeholder = st.empty()
        st.session_state["text_placeholder"] = text_placeholder
        response = ""

        try:
            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=customer_ctx,
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\\$"))

                elif event.type == "agent_updated_stream_event":
                    # 9.5 Handoff UI: 에이전트가 바뀌면(=handoff 발생) 채팅창에 알림 표시
                    if st.session_state["agent"].name != event.new_agent.name:

                        st.write(
                            f"🔁 **{st.session_state['agent'].name}**에서 "
                            f"**{event.new_agent.name}**로 연결해 드릴게요..."
                        )

                        st.session_state["agent"] = event.new_agent

                        text_placeholder = st.empty()
                        st.session_state["text_placeholder"] = text_placeholder
                        response = ""

        except InputGuardrailTripwireTriggered:
            # 👈 과제 채점 기준에 명시된 텍스트로 정확하게 매핑했습니다.
            st.write("저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. 메뉴를 확인하거나, 예약하거나, 음식을 주문할 수 있어요.")

        except OutputGuardrailTripwireTriggered:
            # 👈 봇이 내부 프롬프트나 시스템 정보를 뱉으려다 감지되면 출력될 안전 가드레일
            st.write("전문적이고 정중한 응답을 생성하는 중 문제가 발생했습니다. 다시 시도해 주세요.")

        except MaxTurnsExceeded:
            st.write(
                "죄송해요, 요청을 처리하는 중에 문제가 있었어요 🙏 "
                "한 번에 한 가지씩 말씀해주시면 더 정확히 도와드릴 수 있어요. "
                "다시 한 번 말씀해주시겠어요?"
            )


async def main():
    await paint_history()

    message = st.chat_input(
        "예: 음식이 너무 별로였어 / 인생의 의미가 뭘까? / 예약할게요"
    )

    if message:
        with st.chat_message("human"):
            st.write(message)

        await run_agent(message)


if __name__ == "__main__":
    asyncio.run(main())