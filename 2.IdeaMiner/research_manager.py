# research_manager.py


from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent

import asyncio
from typing import List, Optional


# ---- Small helpers to keep orchestration readable --------------------------------

def _format_plan_prompt(query: str) -> str:
    return f"Query: {query}"

def _format_search_prompt(item: WebSearchItem) -> str:
    return f"Search term: {item.query}\nReason for searching: {item.reason}"

def _format_writer_prompt(query: str, search_results: List[str]) -> str:
    return f"Original query: {query}\nSummarized search results: {search_results}"


class ResearchManager:
    """
    Orchestrates the research pipeline:
      1) Plan searches
      2) Run searches concurrently (capped)
      3) Write report
      4) Email report
    Yields human-readable progress updates along the way.
    """

    def __init__(self, max_parallel_searches: int = 5):
        # A soft cap for concurrent searches; tweak without changing outputs.
        self._sem = asyncio.Semaphore(max_parallel_searches)

    async def run(self, query: str):
        """Run the deep research process, yielding status updates and final markdown."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            link = f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print(link)
            yield link

            # 1) Plan
            print("Starting research...")
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."

            # 2) Execute searches
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."

            # 3) Write report
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."

            # 4) Email
            await self.send_email(report)
            yield "Email sent, research complete"

            # Final output: unchanged public shape (markdown string)
            yield report.markdown_report

    # ---- Each pipeline stage is a focused coroutine --------------------------------

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Ask the planner agent for the set of web searches."""
        print("Planning searches...")
        result = await Runner.run(planner_agent, _format_plan_prompt(query))
        plan = result.final_output_as(WebSearchPlan)
        print(f"Will perform {len(plan.searches)} searches")
        return plan

    async def perform_searches(self, search_plan: WebSearchPlan) -> List[str]:
        """
        Run searches concurrently with a small cap.
        Returns a list of non-empty search summaries (strings).
        """
        print("Searching...")
        tasks = [asyncio.create_task(self._bounded_search(item)) for item in search_plan.searches]

        results: List[str] = []
        completed = 0
        # Consume as they finish, preserving the original progress printing.
        for task in asyncio.as_completed(tasks):
            maybe = await task
            if maybe:
                results.append(maybe)
            completed += 1
            print(f"Searching... {completed}/{len(tasks)} completed")

        print("Finished searching")
        return results

    async def _bounded_search(self, item: WebSearchItem) -> Optional[str]:
        """Enforce concurrency limit and shield individual failures."""
        async with self._sem:
            try:
                res = await Runner.run(search_agent, _format_search_prompt(item))
                return str(res.final_output)
            except Exception:
                # Keep parity with original behavior: swallow failures and return None
                return None

    async def write_report(self, query: str, search_results: List[str]) -> ReportData:
        """Synthesize the final markdown report from all search summaries."""
        print("Thinking about report...")
        res = await Runner.run(writer_agent, _format_writer_prompt(query, search_results))
        print("Finished writing report")
        return res.final_output_as(ReportData)

    async def send_email(self, report: ReportData) -> None:
        """Trigger the email agent with the markdown content."""
        print("Writing email...")
        await Runner.run(email_agent, report.markdown_report)
        print("Email sent")
