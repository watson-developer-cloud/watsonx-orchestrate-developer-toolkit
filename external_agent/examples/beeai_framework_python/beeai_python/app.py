import logging
import sys
import traceback
import warnings

from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import (
    ConditionalRequirement,
)
from beeai_framework.errors import FrameworkError
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.think import ThinkTool
from beeai_framework.adapters.watsonx_orchestrate import (
    WatsonxOrchestrateServer,
    WatsonxOrchestrateServerConfig,
)
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.adapters.watsonx import WatsonxChatModel


from beeai_python.settings import AppSettings
from beeai_python.tools import search_web_tool

warnings.filterwarnings("ignore")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def main() -> None:
    memory = UnconstrainedMemory()
    llm = WatsonxChatModel(
        model_id=AppSettings.watsonx_default_model.removeprefix("watsonx/").lower(),
        api_key=AppSettings.watsonx_api_key,
        project_id=AppSettings.watsonx_project_id,
        base_url=AppSettings.watsonx_url,
        middlewares=[
            GlobalTrajectoryMiddleware(enabled=AppSettings.log_intermediate_steps)
        ],
    )
    agent = RequirementAgent(
        llm=llm,
        memory=memory,
        tools=[ThinkTool(), search_web_tool],
        role="a deep researcher",
        instructions=[
            "Your task is to conduct in-depth research on the given topic.",
            "Before you start, thoroughly prepare a step-by-step plan for how you will solve the task.",
            "After each action, reflect on what you have obtained and what you need to do to gather evidence for the final answer.",
        ],
        middlewares=[
            GlobalTrajectoryMiddleware(
                included=[Tool], enabled=AppSettings.log_intermediate_steps
            )
        ],
        requirements=[
            ConditionalRequirement(ThinkTool, consecutive_allowed=False),
            ConditionalRequirement(
                ThinkTool, force_at_step=1, force_after=[search_web_tool]
            ),
        ],
    )

    config = WatsonxOrchestrateServerConfig(
        port=8080, host="0.0.0.0", api_key=AppSettings.api_key
    )
    server = WatsonxOrchestrateServer(config=config)
    server.register(agent)

    server.serve()


if __name__ == "__main__":
    try:
        main()
    except FrameworkError as e:
        traceback.print_exc()
        sys.exit(e.explain())
