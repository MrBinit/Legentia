from autogen_agentchat.base import TerminationCondition, TerminatedException
from autogen_agentchat.messages import StopMessage

class LegalRiskTerminationCondition(TerminationCondition):
    def __init__(self):
        self._terminated = False

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(self, messages):
        if self._terminated:
            raise TerminatedException("Conversation already terminated.")

        for msg in messages:
            if msg.source == "RiskAnalysisAgent":
                if any(term in msg.content.lower() for term in ["risk", "high risk", "potential liability", "terminate"]):
                    self._terminated = True
                    return StopMessage(
                        content="Risk analysis complete. Terminating session.",
                        source="LegalRiskTerminationCondition"
                    )
        return None
