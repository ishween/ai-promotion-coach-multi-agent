"""State definitions for the LangGraph promotion coach workflow."""
from typing import Dict, Literal, Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# why do we need this? because the opportunity_finder_output is a string and we need to reduce it to a single string
# so we need to reduce the output of the two nodes that are processing the opportunity_finder_output in parallel
def reduce_opportunity_output(old_output: str | None, new_output: str | None) -> str:
    """
    Reducer for opportunity_finder_output - takes the non-empty value.
    
    Args:
        old_output: Previous value (or None)
        new_output: New value (or None)
    
    Returns:
        The non-empty value, preferring right (newer) if both have content
    """
    # Handle None values
    if old_output is None:
        old_output = ""
    if new_output is None:
        new_output = ""
    
    # If old_output is empty or whitespace, use new_output
    if not old_output or not old_output.strip():
        return new_output if new_output else old_output
    # If new_output is empty or whitespace, use old_output
    if not new_output or not new_output.strip():
        return old_output
    # If both have content, prefer new_output (newer value)
    return new_output


class State(TypedDict):
    """
    State for the promotion coach workflow.
    
    This TypedDict defines the structure of state passed between nodes in the LangGraph.
    All fields are optional except those explicitly required.
    """
    # Engineer information
    name: str
    current_level: str
    target_level: str
    discipline: str
    
    # Data files content
    data_files: Dict[str, str]
    
    # Output fields from various analysis nodes
    competency_analyzer_output: str
    gap_analyzer_output: str
    opportunity_finder_output: Annotated[str, reduce_opportunity_output]
    promotion_package_output: str
    
    # Learning preferences
    learning_budget: str
    learning_style: str
    time_availability: str
    wants_course_suggestions: Optional[bool]
    
    # Workflow control
    human_feedback: str
    workflow_type: Literal["first_time", "with_existing_outputs"]
    
    # LangGraph message handling
    messages: Annotated[list[BaseMessage], add_messages]


# Type aliases for better readability
WorkflowType = Literal["first_time", "with_existing_outputs"]

