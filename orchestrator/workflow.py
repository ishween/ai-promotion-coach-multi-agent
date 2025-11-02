"""Workflow execution and orchestration."""
from typing import Dict, Any
from rich.console import Console

from orchestrator.graph import create_graph
from orchestrator.streaming_handler import StreamingHandler
from orchestrator.langgraph_adapter import LangGraphStreamAdapter

console = Console()


async def run_workflow(
    name: str,
    current_level: str,
    target_level: str,
    discipline: str,
    data_files: Dict[str, str],
    previous_outputs: Dict[str, Any],
    learning_budget: str = "Not specified",
    learning_style: str = "online",
    time_availability: str = "Not specified"
) -> Dict[str, Any]:
    """
    Run the promotion coach workflow.
    
    This function orchestrates the entire workflow using LangGraph's native events:
    1. Determines workflow type based on existing outputs
    2. Prepares initial state
    3. Creates and compiles the graph
    4. Executes the workflow with streaming via astream_events
    5. Returns the final state
    
    Args:
        name: Engineer name
        current_level: Current job level
        target_level: Target job level
        discipline: Engineering discipline
        data_files: Dictionary mapping file keys to file contents
        previous_outputs: Dictionary of previous analysis outputs
        learning_budget: Learning budget preference
        learning_style: Preferred learning style
        time_availability: Time availability for learning
    
    Returns:
        Final workflow state dictionary
    """
    # Determine workflow type
    has_competency_output = previous_outputs.get("competency_analyzer") is not None
    workflow_type = "with_existing_outputs" if has_competency_output else "first_time"
    
    # Prepare initial state
    initial_state: Dict[str, Any] = {
        "name": name,
        "current_level": current_level,
        "target_level": target_level,
        "discipline": discipline,
        "data_files": data_files,
        "competency_analyzer_output": previous_outputs.get("competency_analyzer", ""),
        "gap_analyzer_output": previous_outputs.get("gap_analyzer", ""),
        "opportunity_finder_output": previous_outputs.get("opportunity_finder", ""),
        "promotion_package_output": previous_outputs.get("promotion_package", ""),
        "learning_budget": learning_budget,
        "learning_style": learning_style,
        "time_availability": time_availability,
        "wants_course_suggestions": None,  # Will be set by collect_preferences_node
        "human_feedback": "",
        "workflow_type": workflow_type,
        "messages": []
    }
    
    # Create graph
    app = create_graph()
    
    # Config for LangGraph execution
    config = {
        "configurable": {
            "thread_id": f"{name}_{target_level}"
        }
    }
    
    # Map LangGraph node names to display names
    node_display_names = {
        "competency_analyzer": "Competency Analysis",
        "gap_analyzer": "Gap Analysis",
        "promotion_package": "Promotion Package",
        "opportunity_finder": "Opportunity Finder",
        "tools": "Tools",
        "tools_node_with_streaming": "Tools", 
        "tool_node": "Tools",  
    }
    
    handler = StreamingHandler(node_display_names)
    
    # Converts LangGraph events to handler calls
    adapter = LangGraphStreamAdapter(handler, debug=True)  # Set to True for debugging tool events
    
    # Use astream_events (without stream_mode) to get ALL events
    # This gives us: on_chain_start, on_chain_end, on_tool_start, on_tool_end, on_chat_model_stream, etc.
    async for event in app.astream_events(
        initial_state,
        config=config,
        version="v2"
    ):
        # Adapter handles conversion from LangGraph event structure to handler calls
        adapter.process_event(event)
    
    # Verify tool streaming: log if tool events were captured
    tool_events_captured = adapter.get_tool_events_captured()
    if tool_events_captured:
        console.print(f"[dim]✓ Tool streaming verified: {len(tool_events_captured)} tool events captured[/dim]")
    else:
        # Only warn if we expected tool calls (when opportunity_finder should have triggered tools)
        final_state = handler.get_final_state()
        if any(msg.get("tool_calls") for msg in (final_state or initial_state).get("messages", []) if hasattr(msg, "tool_calls")):
            console.print(f"[yellow]⚠ Note: Tool calls detected but no tool events captured. This may be normal if tools completed before events were processed.[/yellow]")
    
    return handler.get_final_state() or initial_state
