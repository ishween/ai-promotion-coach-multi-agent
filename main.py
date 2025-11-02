"""Main entry point for the Promotion Coach terminal application."""
import asyncio
import sys
import warnings

# Suppress Pydantic V1 compatibility warning with Python 3.14+
# This is a known upstream issue with langchain-core - code still works fine
warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.",
    category=UserWarning,
    module="langchain_core._api.deprecation"
)

from cli import (
    display_welcome,
    get_user_input,
    _handle_existing_outputs_flow,
    _handle_first_time_flow
)
from utils import read_data_files, has_previous_outputs


async def main() -> None:
    """Main application loop."""
    display_welcome()
    
    # Get user input
    user_input = get_user_input()
    
    # Load data files
    from rich.console import Console
    console = Console()
    console.print("\n[cyan]Loading data files...[/cyan]")
    data_files = read_data_files()
    
    # Check for previous outputs and route to appropriate flow
    has_previous = has_previous_outputs(user_input.name)
    
    if has_previous:
        await _handle_existing_outputs_flow(user_input, data_files)
    else:
        await _handle_first_time_flow(user_input, data_files)
    
    console.print("\n[bold green]✓ Analysis complete! Outputs have been saved.[/bold green]\n")


def run_application() -> None:
    """Run the application with proper error handling."""
    from rich.console import Console
    console = Console()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    run_application()
