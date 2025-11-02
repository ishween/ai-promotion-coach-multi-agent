"""Routing functions for LangGraph conditional edges."""
from typing import Literal
from orchestrator.state import State

# Route name constants for better maintainability
ROUTE_COMPETENCY_ANALYZER = "competency_analyzer"
ROUTE_GAP_ANALYZER = "gap_analyzer"
ROUTE_TOOLS = "tools"
ROUTE_HUMAN_REVIEW = "human_review"
ROUTE_SAVE_OUTPUTS = "save_outputs"


def route_workflow(state: State) -> Literal["competency_analyzer", "gap_analyzer"]:
    """
    Route workflow based on whether this is first time or has existing outputs.
    
    Decision logic:
    - "first_time": Start with competency analyzer
    - "with_existing_outputs": Skip to gap analyzer
    
    Args:
        state: Current workflow state
    
    Returns:
        Route name: "competency_analyzer" or "gap_analyzer"
    """
    if state["workflow_type"] == "first_time":
        return ROUTE_COMPETENCY_ANALYZER
    else:
        return ROUTE_GAP_ANALYZER


def should_continue_after_opportunity_finder(
    state: State
) -> Literal["human_review", "save_outputs"]:
    """
    Check if human wants to review/edit opportunity finder output.
    
    Decision logic:
    - If human_feedback is "edit": Loop back to human_review
    - Otherwise: Proceed to save_outputs
    
    Args:
        state: Current workflow state
    
    Returns:
        Route name: "human_review" or "save_outputs"
    """
    # Only loop back to human_review if explicitly requested for editing
    if state.get("human_feedback") == "edit":
        return ROUTE_HUMAN_REVIEW
    # Otherwise, go to save_outputs (which will check if everything is ready)
    return ROUTE_SAVE_OUTPUTS


def should_call_tools(state: State) -> Literal["tools", "human_review"]:
    """
    Check if we need to call tools after opportunity finder.
    
    Decision logic:
    - If messages contain tool_calls: Route to tools
    - If opportunity_finder_output is empty but messages exist: Route to tools
    - Otherwise: Route to human_review
    
    Args:
        state: Current workflow state
    
    Returns:
        Route name: "tools" or "human_review"
    """
    # Check if there are messages with tool calls
    messages = state.get("messages", [])
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            return ROUTE_TOOLS
    
    # Check if opportunity_finder_output is empty but we're in opportunity_finder step
    if not state.get("opportunity_finder_output") and messages:
        return ROUTE_TOOLS
    
    return ROUTE_HUMAN_REVIEW

