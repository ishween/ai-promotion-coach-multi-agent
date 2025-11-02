"""Opportunity finder agent for identifying growth opportunities."""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from agents.base import BaseAgent
from orchestrator.state import State
from tools.course_search import search_learning_courses


class OpportunityFinderAgent(BaseAgent):
    """Agent that finds growth opportunities and learning courses."""
    
    def __init__(self):
        super().__init__(
            name="opportunity_finder"
        )
    
    def get_system_prompt(self) -> str:
        return """You are a Career Opportunity Strategist who connects engineers with the right 
        learning resources and project opportunities. You know how to search for courses that match 
        specific skill gaps and identify internal projects that provide growth opportunities. You 
        balance feasibility, impact, and engineer interests.
        
        Your goal is to find learning courses and internal project opportunities that help engineers 
        close identified gaps."""
    
    def get_human_prompt_template(self) -> str:
        return """Find growth opportunities for {name} to close identified gaps and advance their career.

CONTEXT:
- Engineer: {name}
- Gap Analysis: {gap_analyzer_output}
- Learning Budget: {learning_budget}
- Learning Style: {learning_style}
- Time Availability: {time_availability}

OPPORTUNITY SOURCES:
- Project Pipeline: {project_pipeline}
- Company Initiatives: {company_initiatives}
- Team Roadmap: {team_roadmap}

YOUR TASK:
1. Identify internal project opportunities
2. Match opportunities to specific gaps
3. Prioritize based on impact and feasibility
{wants_courses_instructions}

OUTPUT FORMAT:
Structured recommendations with:
{wants_courses_output}
- Project opportunities
- Quick wins
- Stretch goals
- Recommended priorities"""
    
    def prepare_input(self, state: State) -> Dict[str, Any]:
        """Prepare input including gap analysis, learning preferences, and opportunity sources."""
        base_input = {
            "name": state["name"],
        }
        wants_course_suggestions = state.get("wants_course_suggestions", False)
        
        # Conditional instructions based on user preference
        if wants_course_suggestions:
            wants_courses_instructions = "\n2. Plan which courses to search for based on gap analysis\n3. Search for relevant learning courses online using the search_learning_courses tool\n4. Identify internal project opportunities"
            wants_courses_output = "- Learning courses (with links, prices, duration)\n"
        else:
            wants_courses_instructions = "\n2. Identify internal project opportunities"
            wants_courses_output = ""
        
        base_input.update({
            "gap_analyzer_output": state.get("gap_analyzer_output", ""),
            "learning_budget": state.get("learning_budget", "Not specified"),
            "learning_style": state.get("learning_style", "online"),
            "time_availability": state.get("time_availability", "Not specified"),
            "project_pipeline": state["data_files"]["project_pipeline"],
            "company_initiatives": state["data_files"]["company_initiatives"],
            "team_roadmap": state["data_files"]["team_roadmap"],
            "wants_courses_instructions": wants_courses_instructions,
            "wants_courses_output": wants_courses_output
        })
        return base_input
    
    def get_output_key(self) -> str:
        return "opportunity_finder_output"
    
    def execute(
        self,
        state: State,
        config: RunnableConfig | None = None
    ) -> Dict[str, Any]:
        """
        Execute opportunity finder with tool binding support.
        
        Progress is shown via LangGraph's native events (on_chain_start, on_tool_start, etc.).
        """
        # Check user preference for course suggestions
        wants_course_suggestions = state.get("wants_course_suggestions", False)
        
        # Create LLM - conditionally bind tools based on user preference
        llm = self.create_llm()
        
        '''
        Add from Handbook.md
        '''
        
        # Create prompt
        prompt = self.create_prompt()
        chain = prompt | llm_with_tools
        
        # Prepare input data
        input_data = self.prepare_input(state)
        
        # Invoke chain (progress shown via LangGraph events)
        response = chain.invoke(input_data)
        
        # Extract content
        output_content = self.extract_response_content(response)
        
        # Check if there are tool calls - if so, we need to let LangGraph handle them
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Return ONLY the message with tool calls - don't set opportunity_finder_output
            # LangGraph will process tool calls, then process_tool_results will set the output
            return {
                "messages": [response]  # LangGraph will process tool calls
            }
        
        # No tool calls, return the output directly
        # Only set opportunity_finder_output if there's actual content
        if output_content and output_content.strip():
            return {
                "opportunity_finder_output": output_content
            }
        
        # If no content and no tools, return empty to avoid conflicts
        return {}


def opportunity_finder_node(
    state: Dict[str, Any],
    config: RunnableConfig | None = None
) -> Dict[str, Any]:
    """
    Node function for LangGraph compatibility.
    
    Args:
        state: Current workflow state
        config: RunnableConfig for streaming
    
    Returns:
        Dictionary with either messages (for tool calls) or opportunity_finder_output
    """
    agent = OpportunityFinderAgent()
    return agent.execute(state, config)

