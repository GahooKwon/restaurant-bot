import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import CustomerContext, InputGuardRailOutput, HandoffData
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent


input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    손님의 요청이 메뉴 문의, 주문, 또는 테이블 예약과 관련이 있는지 확인하세요.
    레스토랑과 전혀 관련 없는 주제(예: 정치, 코딩, 다른 가게 문의 등)라면 오프토픽으로 판단하고
    트립와이어를 발생시킬 이유(reason)를 작성하세요.
    인사나 간단한 스몰토크는 괜찮지만, 레스토랑 메뉴/주문/예약과 무관한 요청은 도와주지 마세요.
    """,
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[CustomerContext],
    agent: Agent[CustomerContext],
    input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[CustomerContext],
    agent: Agent[CustomerContext],
):
    return f"""
{RECOMMENDED_PROMPT_PREFIX}

당신은 레스토랑의 1차 응대 담당(Triage Agent)입니다.
손님을 이름으로 부르며, 손님이 무엇을 원하는지 파악한 뒤 적절한 전문가에게 연결(handoff)하는 역할만 합니다.
당신은 {wrapper.context.name} 손님과 대화하고 있습니다. {"이 손님은 VIP 손님입니다. 더욱 정중하게 응대하세요." if wrapper.context.vip else ""}

당신이 도와줄 수 있는 분류는 다음과 같습니다:
1. 메뉴, 재료, 알레르기 질문 -> Menu Agent로 연결
2. 음식 주문 의사 (메뉴명이 없어도 "주문할게요"라고만 해도) -> Order Agent로 연결
3. 테이블 예약 의사 (날짜/시간이 없어도 "예약할게요"라고만 해도) -> Reservation Agent로 연결

[🚨 중요 규칙]:
- 손님의 요청 종류가 명확하면 직접 답변하지 말고 **반드시 즉시 handoff 도구를 호출**하여 전문가에게 연결하세요.
- 예를 들어 "예약하고 싶어"라는 말에 "성함이 어떻게 되시나요?"라고 묻지 말고 곧바로 Reservation Agent로 넘기세요. 구체적인 질문은 전문가의 역할입니다.
- 단 한 마디의 실질적인 답변 텍스트(질문 포함)도 생성하지 말고 오직 handoff 도구만 호출하세요.
- 다른 전문가가 당신에게 손님을 다시 돌려보낸 경우, 방금 어디서 왔는지는 무시하고 현재 메시지에 맞는 전문가에게 다시 연결하세요.
"""


def handle_handoff(
    wrapper: RunContextWrapper[CustomerContext],
    input_data: HandoffData,
):
    with st.sidebar:
        st.write(
            f"""
            **🔁 Handoff 발생**
            - 연결된 곳: {input_data.to_agent_name}
            - 요청 종류: {input_data.request_type}
            - 요청 내용: {input_data.request_description}
            - 이유: {input_data.reason}
            """
        )


def make_handoff(agent):
    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )


triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[
        off_topic_guardrail,
    ],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
    ],
)

menu_agent.handoffs = [
    make_handoff(triage_agent),
]

order_agent.handoffs = [
    make_handoff(triage_agent),
]

reservation_agent.handoffs = [
    make_handoff(triage_agent),
]