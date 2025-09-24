# planner_agent.py


from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 5  


def _instruction(how_many: int) -> str:
    """
    Build a focused instruction that nudges the model to produce exactly `how_many` items.
    """
    header = "You are a helpful research assistant."
    task = (
        "Given a user query, propose a targeted set of web searches that, when combined, "
        "enable a comprehensive answer. Focus on breadth + key depth: include primary sources, "
        "recent analyses, and authoritative references."
    )
    format_hint = f"Return exactly {how_many} search terms."
    return f"{header} {task} {format_hint}"


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search advances the overall research goal.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="The set of searches to perform.")


INSTRUCTIONS = _instruction(HOW_MANY_SEARCHES)

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)
