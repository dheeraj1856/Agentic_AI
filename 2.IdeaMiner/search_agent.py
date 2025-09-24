# search_agent.py


from agents import Agent, WebSearchTool, ModelSettings

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, perform a web search and produce a concise synthesis. "
    "Return 2–3 short paragraphs, under 300 words total. Capture core facts and signals from top sources. "
    "Omit filler, meta-text, and commentary. Output only the summary text."
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
