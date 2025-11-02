"""Node implementations for the LangGraph workflow."""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode

from orchestrator.state import State
from tools.course_search import search_learning_courses


def opportunity_finder_with_tools(
    state: State,
    config: RunnableConfig | None = None
) -> Dict[str, Any]:
    """
    Opportunity finder node that may return tool calls.
    
    Since collect_preferences always runs before this node, if wants_course_suggestions
    is explicitly set (not None), it means preferences were just collected and we should
    regenerate output even if old output exists.
    
    Args:
        state: Current workflow state
        config: RunnableConfig (kept for compatibility)
    
    Returns:
        Dictionary with either messages (for tool calls) or opportunity_finder_output
    """
    existing_output = state.get("opportunity_finder_output", "").strip()
    wants_course_suggestions = state.get("wants_course_suggestions", None)
    
    # Since collect_preferences ALWAYS runs immediately before this node:
    # - If wants_course_suggestions is set (True or False, not None), preferences were just collected
    # - Always regenerate when coming from collect_preferences, even if old output exists
    # - This ensures fresh output with updated preferences
    if existing_output and wants_course_suggestions is None:
        # Only skip if no preferences collected AND old output exists
        # This is rare - usually collect_preferences sets this value
        return {}
    
    # Preferences were just collected (wants_course_suggestions is True/False) OR no old output
    # Always regenerate to get fresh output with current preferences
    from agents.opportunity_finder import opportunity_finder_node
    result = opportunity_finder_node(state, config)
    
    # If we're regenerating, ensure we clear old output by overwriting it
    # The reducer will handle merging, but since we have new output, it should win
    return result


def tools_node_with_streaming(
    state: State,
    config: RunnableConfig | None = None
) -> Dict[str, Any]:
    """
    Wrapper for ToolNode.
    
    Tool execution progress is shown via LangGraph's native events (on_tool_start, on_tool_end).
    
    Args:
        state: Current workflow state
        config: RunnableConfig (kept for compatibility)
    
    Returns:
        Dictionary with tool execution results
    """
    # Execute the actual tool node (progress shown via LangGraph events)
    tools = [search_learning_courses]
    tool_node = ToolNode(tools)
    result = tool_node.invoke(state, config)
    
    return result


def collect_learning_preferences_node(state: State) -> Dict[str, Any]:
    """
    Collect learning preferences from user before running opportunity finder.
    
    First asks if user wants course suggestions. Only if yes, asks for learning preferences.
    Always clears opportunity_finder_output to force regeneration with new preferences.
    
    Args:
        state: Current workflow state
    
    Returns:
        Dictionary with wants_course_suggestions, learning preferences, and cleared opportunity_finder_output
    """
    import sys
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    
    console = Console()
    
    # Force output flush to ensure message appears immediately
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Add clear indication that we're entering preferences collection
    console.print("\n[bold yellow]📋 Collecting preferences for opportunity finder...[/bold yellow]")
    sys.stdout.flush()
    
    wants_course_suggestions = state.get("wants_course_suggestions", None)
    target_level = state.get("target_level", "")
    
    result = {}
    
    # Clear old output - use a special marker that reducer will recognize
    # The reducer will keep old output if new is empty, so we need to bypass it
    # We'll handle this in opportunity_finder_with_tools instead
    
    # FIRST: Always ask about course suggestions before opportunity finder
    console.print("\n[bold cyan]Course Suggestions:[/bold cyan]")
    sys.stdout.flush()
    
    # Use the existing value as default if it was set before
    default_value = wants_course_suggestions if wants_course_suggestions is not None else True
    
    # Ensure prompt is visible and flushed
    sys.stdout.flush()
    wants_course_suggestions = Confirm.ask(
        f"[yellow]Do you want me to suggest learning courses for your {target_level}?[/yellow]",
        default=default_value
    )
    result["wants_course_suggestions"] = wants_course_suggestions
    sys.stdout.flush()
    
    # ONLY if they want course suggestions, ask for learning preferences
    if wants_course_suggestions:
        console.print()
        console.print("[bold cyan]Learning Preferences:[/bold cyan]\n")
        
        learning_budget = Prompt.ask(
            "[yellow]Learning Budget[/yellow]",
            default="Not specified"
        )
        learning_style = Prompt.ask(
            "[yellow]Learning Style[/yellow]",
            choices=["online", "in-person", "hybrid", "any"],
            default="online"
        )
        time_availability = Prompt.ask(
            "[yellow]Time Availability[/yellow]",
            default="Not specified"
        )
        
        result.update({
            "learning_budget": learning_budget,
            "learning_style": learning_style,
            "time_availability": time_availability
        })
    
    console.print()  # Add spacing after section
    
    return result


def human_review_node(state: State) -> Dict[str, Any]:
    """
    Human-in-the-loop node for reviewing and editing opportunity finder output.
    
    Displays the opportunity finder output and allows the user to:
    - Approve and continue
    - Edit the output
    - Skip (keep as is)
    
    Args:
        state: Current workflow state
    
    Returns:
        Dictionary with human_feedback and optionally edited opportunity_finder_output
    """
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    console.print("\n[bold cyan]=== Opportunity Finder Output - Human Review ===[/bold cyan]\n")
    
    output = state.get("opportunity_finder_output", "")
    if output:
        # Display full output in a formatted panel for review and approval
        console.print(Panel(
            output,
            title="[bold yellow]Full Opportunity Finder Output[/bold yellow]",
            border_style="cyan",
            padding=(1, 2),
            width=None  # Use full terminal width
        ))
        console.print()  # Add spacing
    else:
        console.print("[yellow]Warning: No opportunity finder output found.[/yellow]\n")
    
    console.print("[bold yellow]You can now review and edit the output.[/bold yellow]")
    console.print("[dim]Enter 'edit' to modify, 'approve' to continue, or 'skip' to keep as is:[/dim]")
    
    user_input = input().strip().lower()
    
    if user_input == "edit":
        console.print("\n[cyan]Enter your edited version (press Ctrl+D or Ctrl+Z when finished):[/cyan]")
        try:
            edited_lines = []
            while True:
                line = input()
                edited_lines.append(line)
        except EOFError:
            edited_output = "\n".join(edited_lines)
            return {
                "opportunity_finder_output": edited_output,
                "human_feedback": "edited"
            }
    elif user_input == "approve":
        return {
            "human_feedback": "approved"
        }
    else:
        return {
            "human_feedback": "skipped"
        }


def save_outputs_node(state: State) -> Dict[str, Any]:
    """
    Save all outputs to files - only executes when all required outputs are ready.
    
    This node checks if all required outputs are available before saving:
    - For "first_time": needs promotion_package, opportunity_finder, and human_feedback
    - For "with_existing_outputs": needs opportunity_finder and human_feedback
    
    Args:
        state: Current workflow state
    
    Returns:
        Dictionary with success message, or empty dict if not ready yet
    """
    import os
    from utils import OUTPUTS_FOLDER, save_output, generate_combined_html_report
    from pathlib import Path
    
    # Check if we have everything required before saving
    if state["workflow_type"] == "first_time":
        # For first-time workflow, need both promotion_package and opportunity_finder outputs
        has_promotion = bool(state.get("promotion_package_output", "").strip())
        has_opportunity = bool(state.get("opportunity_finder_output", "").strip())
        human_done = bool(state.get("human_feedback", "").strip())
        
        if not (has_promotion and has_opportunity and human_done):
            # Not ready yet, skip saving (this node will be called again when other path completes)
            return {}
    else:
        # For existing outputs workflow, just need opportunity_finder and human_review
        has_opportunity = bool(state.get("opportunity_finder_output", "").strip())
        human_done = bool(state.get("human_feedback", "").strip())
        
        if not (has_opportunity and human_done):
            # Not ready yet, skip saving
            return {}
    
    # All required outputs are ready, proceed with saving
    # Always save/regenerate to ensure HTML files are created even if JSON exists
    name = state["name"]
    
    # Collect outputs for saving and combined report
    outputs = {}
    
    if state.get("competency_analyzer_output"):
        save_output(name, "competency_analyzer", state["competency_analyzer_output"])
        outputs["competency_analyzer"] = state["competency_analyzer_output"]
    
    if state.get("gap_analyzer_output"):
        save_output(name, "gap_analyzer", state["gap_analyzer_output"])
        outputs["gap_analyzer"] = state["gap_analyzer_output"]
    
    if state.get("opportunity_finder_output"):
        save_output(name, "opportunity_finder", state["opportunity_finder_output"])
        outputs["opportunity_finder"] = state["opportunity_finder_output"]
    
    if state.get("promotion_package_output"):
        save_output(name, "promotion_package", state["promotion_package_output"])
        outputs["promotion_package"] = state["promotion_package_output"]
    
    # Generate and save combined HTML report (always regenerate to ensure it exists)
    if outputs:
        combined_html = generate_combined_html_report(name, outputs)
        report_path = OUTPUTS_FOLDER / f"{name}_full_report.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(combined_html)
    
    return {"message": "Outputs saved successfully"}

