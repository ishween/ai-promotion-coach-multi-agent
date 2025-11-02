"""Graph construction and compilation for the LangGraph workflow."""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from orchestrator.state import State
from orchestrator.nodes import (
    opportunity_finder_with_tools,
    collect_learning_preferences_node,
    human_review_node,
    save_outputs_node,
    tools_node_with_streaming,
)
from orchestrator.routing import (
    route_workflow,
    should_continue_after_opportunity_finder,
    should_call_tools,
    ROUTE_COMPETENCY_ANALYZER,
    ROUTE_GAP_ANALYZER,
    ROUTE_TOOLS,
    ROUTE_HUMAN_REVIEW,
    ROUTE_SAVE_OUTPUTS,
)
from orchestrator.tools import process_tool_results
from agents.competency_analyzer import competency_analyzer_node
from agents.gap_analyzer import gap_analyzer_node
from agents.promotion_package import promotion_package_node


def create_graph():
    """
    Create and compile the LangGraph workflow.
    
    The workflow structure:
    1. Entry point routes to either competency_analyzer or gap_analyzer
    2. For first_time: competency_analyzer -> (gap_analyzer + promotion_package in parallel)
    3. gap_analyzer -> collect_preferences -> opportunity_finder
    4. opportunity_finder -> (tools if needed) -> process_tool_results -> human_review
    5. human_review -> save_outputs (or loops back if editing)
    6. promotion_package -> save_outputs (waits for other path to complete)
    7. save_outputs -> END
    
    Returns:
        Compiled LangGraph application with memory checkpointing
    """
    # Create the graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("route_workflow", lambda state: state)  # Entry node that routes
    workflow.add_node("competency_analyzer", competency_analyzer_node)
    '''
    Add from Handbook.md
    '''
    workflow.add_node("collect_preferences", collect_learning_preferences_node)
    workflow.add_node("opportunity_finder", opportunity_finder_with_tools)
    workflow.add_node("tools", tools_node_with_streaming)
    workflow.add_node("process_tool_results", process_tool_results)
    '''
    Add from Handbook.md
    '''
    workflow.add_node("save_outputs", save_outputs_node)
    
    # Set entry point
    workflow.set_entry_point("route_workflow")
    
    # Route from entry point
    workflow.add_conditional_edges(
        "route_workflow",
        route_workflow,
        {
            ROUTE_COMPETENCY_ANALYZER: "competency_analyzer",
            ROUTE_GAP_ANALYZER: "gap_analyzer"
        }
    )
    
    # Define edges for first-time workflow
    # After competency_analyzer, run gap_analyzer and promotion_package in parallel
    '''
    Add from Handbook.md
    '''
    
    # After gap_analyzer, collect learning preferences before opportunity_finder
    workflow.add_edge("gap_analyzer", "collect_preferences")
    
    # After collecting preferences, run opportunity_finder
    workflow.add_edge("collect_preferences", "opportunity_finder")
    
    # After opportunity_finder, check if tools need to be called
    '''
    Add from Handbook.md
    '''
    
    # After tools, process results
    workflow.add_edge("tools", "process_tool_results")
    workflow.add_edge("process_tool_results", "human_review")
    
    # After human review, check if we should save or get more feedback
    workflow.add_conditional_edges(
        "human_review",
        should_continue_after_opportunity_finder,
        {
            ROUTE_HUMAN_REVIEW: "human_review",  # Loop back if more edits needed
            ROUTE_SAVE_OUTPUTS: "save_outputs"  # Route directly to save_outputs
        }
    )
    
    # After promotion_package, go directly to save_outputs
    # save_outputs_node will check if all requirements are met before actually saving
    # If not ready, it returns early and will be called again from the other path
    workflow.add_edge("promotion_package", "save_outputs")
    
    # Save outputs goes to END
    # The save_outputs_node itself handles checking if everything is ready
    # If not ready when called from one path, it just returns {} and waits
    # When called from the other path, everything should be ready
    workflow.add_edge("save_outputs", END)
    
    # Compile with memory for checkpointing
    memory = MemorySaver()
    '''
    Add from Handbook.md
    '''

    
    return app

