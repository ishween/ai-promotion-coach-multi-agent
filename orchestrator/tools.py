"""Tool processing and integration for the workflow."""
from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from orchestrator.state import State
from utils import create_llm


class ToolProcessor:
    """
    Processes tool results and generates final opportunity finder output.
    
    This class encapsulates the logic for handling tool execution results
    and synthesizing them into a final opportunity analysis.
    """
    
    def __init__(self, config: RunnableConfig | None = None):
        """
        Initialize ToolProcessor.
        
        Args:
            config: RunnableConfig (kept for compatibility, not used)
        """
        self.config = config
    
    def process(
        self,
        state: State,
        tool_results: list[str],
        ai_message: Any
    ) -> Dict[str, Any]:
        """
        Process tool results and generate final output.
        
        Progress is shown via LangGraph's native events.
        
        Args:
            state: Current workflow state
            tool_results: List of tool execution results as strings
            ai_message: The AI message that triggered the tool calls
        
        Returns:
            Dictionary with opportunity_finder_output and cleared messages
        """
        # Check if preferences were just updated
        # If preferences were collected (wants_course_suggestions is not None), regenerate
        wants_course_suggestions = state.get("wants_course_suggestions", None)
        existing_output = state.get("opportunity_finder_output", "").strip()
        
        # Only skip if no preferences collected AND old output exists
        if existing_output and wants_course_suggestions is None:
            return {"messages": []}
        
        # Generate final response with tool results
        gap_analysis = state.get("gap_analyzer_output", "")
        data_files = state.get("data_files", {})
        
        final_messages = [
            SystemMessage(
                content="You are a Career Opportunity Strategist who connects "
                       "engineers with the right learning resources and project opportunities."
            ),
            HumanMessage(content=f"""Create a comprehensive opportunity analysis based on:

Gap Analysis:
{gap_analysis}

Course Search Results:
{chr(10).join(tool_results)}

Opportunity Sources:
- Project Pipeline: {data_files.get('project_pipeline', 'N/A')}
- Company Initiatives: {data_files.get('company_initiatives', 'N/A')}
- Team Roadmap: {data_files.get('team_roadmap', 'N/A')}

Learning Preferences:
- Budget: {state.get('learning_budget', 'Not specified')}
- Style: {state.get('learning_style', 'online')}
- Time: {state.get('time_availability', 'Not specified')}

Provide structured recommendations with:
- Learning courses (from search results, with links, prices, duration)
- Project opportunities
- Quick wins
- Stretch goals
- Recommended priorities"""),
        ]
        
        llm = create_llm()
        response = llm.invoke(final_messages)
        
        return {
            "opportunity_finder_output": response.content,
            "messages": []  # Clear messages after processing
        }
    
    def extract_tool_results(self, messages: list) -> tuple[list[str], Any]:
        """
        Extract tool results and AI message from state messages.
        
        Args:
            messages: List of messages from state
        
        Returns:
            Tuple of (tool_results, ai_message)
        """
        tool_results = []
        ai_message = None
        
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                ai_message = msg
            elif isinstance(msg, ToolMessage) or (
                hasattr(msg, "content") and (
                    "courses_found" in str(msg.content) or
                    "skill_gap" in str(msg.content) or
                    isinstance(msg, ToolMessage)
                )
            ):
                tool_results.append(str(msg.content))
        
        return tool_results, ai_message


def process_tool_results(state: State, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """
    Process tool results and generate final opportunity finder output.
    
    This is the node function interface for LangGraph.
    
    Args:
        state: Current workflow state
        config: RunnableConfig for streaming
    
    Returns:
        Dictionary with updated state fields
    """
    processor = ToolProcessor(config)
    
    # Check if preferences were just updated (wants_course_suggestions is set, not None)
    # If preferences were just collected, regenerate even if old output exists
    wants_course_suggestions = state.get("wants_course_suggestions", None)
    existing_output = state.get("opportunity_finder_output", "").strip()
    
    # Only skip if no preferences were collected (None) AND output exists
    # Otherwise, process tool results to generate fresh output
    if existing_output and wants_course_suggestions is None:
        return {"messages": []}
    
    messages = state.get("messages", [])
    tool_results, ai_message = processor.extract_tool_results(messages)
    
    if ai_message and tool_results:
        return processor.process(state, tool_results, ai_message)
    
    # If no tools were called or no tool results, check if we already have output
    if state.get("opportunity_finder_output"):
        return {"messages": []}
    
    # Fallback: generate output without tool results
    gap_analysis = state.get("gap_analyzer_output", "")
    llm = create_llm()
    final_messages = [
        SystemMessage(content="You are a Career Opportunity Strategist."),
        HumanMessage(content=f"Gap Analysis:\n{gap_analysis}\n\nProvide opportunity recommendations."),
    ]
    response = llm.invoke(final_messages)
    return {
        "opportunity_finder_output": response.content,
        "messages": []
    }

