from pydantic import BaseModel
from typing import Optional


class CustomerContext(BaseModel):
    """대화 전체에서 공유되는 손님 컨텍스트 (강의 9.1 Context Management 패턴)"""

    customer_id: int
    name: str
    vip: bool = False
    phone: Optional[str] = None


class InputGuardRailOutput(BaseModel):
    """오프토픽 여부를 판단하는 가드레일 에이전트의 출력 (강의 9.3 패턴)"""

    is_off_topic: bool
    reason: str


class HandoffData(BaseModel):
    """handoff 발생 시 전달되는 데이터. 사이드바 UI에 표시하기 위해 사용 (강의 9.4, 9.5 패턴)"""

    to_agent_name: str
    request_type: str
    request_description: str
    reason: str
