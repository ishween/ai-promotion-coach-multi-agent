"""CLI utilities and UI functions for the Promotion Coach terminal application."""
from dataclasses import dataclass
from typing import Dict
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from orchestrator import run_workflow
from utils import (
    load_all_outputs,
    display_output_table,
    prompt_for_additional_info,
    update_data_file,
    OUTPUTS_FOLDER
)

console = Console()


# Constants
DATA_FILE_MAPPING = {
    "project_contributions": "project_contributions.txt",
    "manager_notes": "manager_notes.txt",
    "performance_reviews": "performance_reviews.txt",
    "peer_feedback": "peer_feedback.txt",
    "self_assessment": "self_assessment.txt",
    "project_pipeline": "project_pipeline.txt",
    "company_initiatives": "company_initiatives.txt",
    "team_roadmap": "team_roadmap.txt",
}

OUTPUT_TYPE_KEYS = [
    "competency_analyzer",
    "gap_analyzer",
    "opportunity_finder",
    "promotion_package"
]

DEFAULT_LEARNING_PREFERENCES = {
    "learning_budget": "Not specified",
    "learning_style": "online",
    "time_availability": "Not specified"
}

# python decorator to convert the class to a dataclass and add type hints (boilerplate code)
@dataclass
class UserInput:
    """Structured user input data."""
    name: str
    current_level: str
    target_level: str
    discipline: str


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    final_state: Dict
    name: str


def display_welcome() -> None:
    """Display welcome message."""
    welcome_text = """
    # Promotion Coach System
    
    Welcome! This system helps engineers prepare for promotions by:
    - Analyzing competency requirements
    - Identifying skill gaps
    - Finding growth opportunities
    - Creating promotion packages
    """
    console.print(welcome_text)
    console.print("[bold green]Welcome to Promotion Coach System![/bold green]\n")


def get_user_input() -> UserInput:
    """Get basic input from user."""
    console.print("\n[bold cyan]Please provide the following information:[/bold cyan]\n")
    
    name = Prompt.ask("[yellow]Engineer Name[/yellow]")
    current_level = Prompt.ask("[yellow]Current Level[/yellow] (e.g., L4, Senior)")
    target_level = Prompt.ask("[yellow]Target Level[/yellow] (e.g., L5, Staff)")
    discipline = Prompt.ask("[yellow]Discipline[/yellow] (e.g., Software Engineering)", default="Software Engineering")
    
    return UserInput(name=name, current_level=current_level, target_level=target_level, discipline=discipline)


def display_workflow_summary(state: Dict, name: str) -> None:
    """Display brief summary and location of outputs after workflow completion."""
    console.print("\n[bold green]✓ Analysis complete![/bold green]\n")
    
    # Count available outputs
    outputs = {
        "Competency Analysis": state.get("competency_analyzer_output", ""),
        "Gap Analysis": state.get("gap_analyzer_output", ""),
        "Opportunity Finder": state.get("opportunity_finder_output", ""),
        "Promotion Package": state.get("promotion_package_output", ""),
    }
    
    available_count = sum(1 for content in outputs.values() if content and content.strip())
    
    console.print(f"[cyan]Generated {available_count} analysis outputs[/cyan]")
    console.print(f"\n[bold yellow]📄 View outputs in browser:[/bold yellow]")
    console.print(f"   • Individual reports: {OUTPUTS_FOLDER}/{name}_*.html")
    console.print(f"   • Combined report: {OUTPUTS_FOLDER}/{name}_full_report.html")
    console.print(f"\n[dim]All outputs saved to: {OUTPUTS_FOLDER}[/dim]\n")


def display_outputs_table(outputs: Dict, name: str) -> None:
    """Display outputs in a simple status table."""
    from utils import load_output
    
    # Load any missing outputs from saved files
    for key in OUTPUT_TYPE_KEYS:
        if not outputs.get(key) or not outputs[key].strip():
            # Try to load from saved file
            saved_content = load_output(name, key)
            if saved_content:
                outputs[key] = saved_content
    
    table = Table(title="Analysis Outputs Status", show_header=True, header_style="bold magenta")
    table.add_column("Output Type", style="cyan", no_wrap=True)
    table.add_column("Status", style="green", justify="center")
    
    for output_type, content in outputs.items():
        status = "Available" if content and content.strip() else "Not Available"
        status_style = "green" if status == "Available" else "red"
        table.add_row(
            output_type.replace("_", " ").title(),
            f"[{status_style}]{status}[/{status_style}]"
        )
    
    console.print(table)


def _extract_outputs_from_state(state: Dict) -> Dict[str, str]:
    """Extract all output contents from workflow state."""
    return {
        "competency_analyzer": state.get("competency_analyzer_output", ""),
        "gap_analyzer": state.get("gap_analyzer_output", ""),
        "opportunity_finder": state.get("opportunity_finder_output", ""),
        "promotion_package": state.get("promotion_package_output", ""),
    }


def _update_data_files_if_needed(data_files: Dict) -> Dict:
    """Prompt user for additional data file information and update files if needed."""
    if not Confirm.ask("\n[cyan]Would you like to provide additional information for data files?[/cyan]"):
        return data_files
    
    updated_files = prompt_for_additional_info(data_files)
    data_files.update(updated_files)
    
    # Update actual files on disk
    for key, filename in DATA_FILE_MAPPING.items():
        if key in updated_files:
            update_data_file(filename, updated_files[key])
    
    return data_files


def _handle_post_workflow_display(final_state: Dict, name: str) -> None:
    """Handle all post-workflow display logic."""
    display_workflow_summary(final_state, name)
    
    outputs_dict = _extract_outputs_from_state(final_state)
    
    if Confirm.ask("\n[cyan]Would you like to view outputs status table?[/cyan]"):
        display_outputs_table(outputs_dict, name)


async def _run_workflow_and_display(
    user_input: UserInput,
    data_files: Dict,
    previous_outputs: Dict
) -> None:
    """Run workflow and display results."""
    console.print("\n[bold green]Running analysis workflow...[/bold green]\n")
    
    final_state = await run_workflow(
        name=user_input.name,
        current_level=user_input.current_level,
        target_level=user_input.target_level,
        discipline=user_input.discipline,
        data_files=data_files,
        previous_outputs=previous_outputs,
        learning_budget=DEFAULT_LEARNING_PREFERENCES["learning_budget"],
        learning_style=DEFAULT_LEARNING_PREFERENCES["learning_style"],
        time_availability=DEFAULT_LEARNING_PREFERENCES["time_availability"]
    )
    
    _handle_post_workflow_display(final_state, user_input.name)


async def _handle_existing_outputs_flow(user_input: UserInput, data_files: Dict) -> None:
    """Handle workflow when previous outputs exist."""
    console.print(f"\n[bold yellow]Previous outputs found for {user_input.name}![/bold yellow]")
    previous_outputs = load_all_outputs(user_input.name)
    
    # Display previous outputs
    table = display_output_table(previous_outputs)
    console.print(table)
    
    # Update data files if user wants to
    data_files = _update_data_files_if_needed(data_files)
    
    # Ask if user wants to run analysis
    if Confirm.ask("\n[cyan]Would you like to run the analysis workflow?[/cyan]"):
        await _run_workflow_and_display(user_input, data_files, previous_outputs)
    else:
        console.print("[yellow]Analysis workflow skipped.[/yellow]")


async def _handle_first_time_flow(user_input: UserInput, data_files: Dict) -> None:
    """Handle workflow for first-time analysis."""
    console.print(f"\n[bold green]First time analysis for {user_input.name}. Running full workflow...[/bold green]\n")
    
    await _run_workflow_and_display(user_input, data_files, previous_outputs={})

