# writer_agent.py


from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher compiling a cohesive report from a user query and summarized findings.\n"
    "First, design a logical outline (sections/subsections) that tells a complete story. Then write the report.\n"
    "The final result MUST be markdown, comprehensive, and long-form (aim ≥ 1000 words). "
    "Favor clarity, structure, and citations-in-text (plain text) where relevant."
)

class ReportData(BaseModel):
    short_summary: str = Field(description="A brief 2–3 sentence executive summary.")
    markdown_report: str = Field(description="The complete report in markdown.")
    follow_up_questions: list[str] = Field(description="Concrete next areas to explore.")

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)
