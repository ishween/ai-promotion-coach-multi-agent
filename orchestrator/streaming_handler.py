"""Abstract streaming handler - framework-agnostic business logic for progress display."""
from typing import Dict, Any, Set, Optional
from rich.console import Console

console = Console()


class StreamingHandler:
    """
    Abstract streaming handler that manages progress display logic.
    
    This class contains pure business logic that is independent of LangGraph or any
    specific event framework. It handles:
    - Progress display (starting, generating, complete messages)
    - State tracking (active nodes, tools, outputs)
    - Deduplication (preventing duplicate messages)
    
    Framework-specific adapters convert events from their source to calls on this handler.
    """
    
    def __init__(self, node_display_names: Dict[str, str]):
        """
        Initialize streaming handler.
        
        Args:
            node_display_names: Mapping of node keys to human-readable display names
        """
        self.node_display_names = node_display_names
        
        # State tracking variables
        self.active_node: Optional[str] = None
        self.active_tools: Dict[str, bool] = {}  # tool_name -> is_active
        self.generation_shown: Set[str] = set()  # Nodes that have shown "Generating..." message
        self.logged_outputs: Set[str] = set()  # Outputs that have shown "saved" message
        self.final_state: Optional[Dict[str, Any]] = None
    
    def _match_node_name(self, node_name: str) -> Optional[str]:
        """
        Match event node name to a known node key.
        
        Handles both exact matches and nested names (e.g., "gap_analyzer.gap_analyzer_node").
        
        Args:
            node_name: Node name from event
        
        Returns:
            Matched node key or None
        """
        if node_name in self.node_display_names:
            return node_name
        
        # Try to match by checking if any node name is contained in the event name
        for node_key in self.node_display_names:
            if node_key in node_name or node_name.endswith(f".{node_key}"):
                return node_key
        
        return None
    
    def handle_node_start(self, node_name: str) -> None:
        """
        Handle node start event - show progress when nodes begin execution.
        
        Args:
            node_name: Name of the node that started
        """
        matched_node = self._match_node_name(node_name)
        
        if matched_node:
            display_name = self.node_display_names[matched_node]
            console.print(f"\n[yellow]🔍 Starting {display_name}...[/yellow]")
            self.generation_shown.discard(matched_node)  # Reset for this run
            self.active_node = matched_node
    
    def handle_node_generating(self, node_name: str) -> None:
        """
        Handle node generating event - show generating status once per node.
        
        Args:
            node_name: Name of the node that is generating
        """
        matched_node = self._match_node_name(node_name)
        
        # Fallback: if no direct match but we have an active_node, check if event belongs to it
        if not matched_node and self.active_node:
            if self.active_node in node_name or node_name.endswith(f".{self.active_node}"):
                matched_node = self.active_node
        
        if matched_node and matched_node not in self.generation_shown:
            display_name = self.node_display_names[matched_node]
            console.print(f"[blue]💭 Generating {display_name}...[/blue]")
            self.generation_shown.add(matched_node)
    
    def handle_node_end(self, node_name: str, output: Dict[str, Any]) -> None:
        """
        Handle node end event - show completion and track state.
        
        Args:
            node_name: Name of the node that completed
            output: Output dictionary from the node
        """
        matched_node = self._match_node_name(node_name)
        
        # Update final_state from node outputs
        if isinstance(output, dict):
            if self.final_state:
                self.final_state.update(output)
            else:
                self.final_state = output.copy()
            
            # Show completion message
            if matched_node and self.active_node == matched_node:
                display_name = self.node_display_names[matched_node]
                console.print(f"[green]✅ {display_name} complete[/green]")
                self.active_node = None
            
            # Log completion messages for each output type
            self._log_outputs(output)
    
    def _log_outputs(self, output: Dict[str, Any]) -> None:
        """
        Log completion messages for outputs.
        
        Args:
            output: Output dictionary from node
        """
        output_checks = [
            ("competency_analyzer_output", "competency_analyzer", "Competency analysis"),
            ("gap_analyzer_output", "gap_analyzer", "Gap analysis"),
            ("promotion_package_output", "promotion_package", "Promotion package"),
            ("opportunity_finder_output", "opportunity_finder", "Opportunity finder")
        ]
        
        for output_key, log_key, display_msg in output_checks:
            if output_key in output and output.get(output_key):
                if log_key not in self.logged_outputs:
                    console.print(f"[green]✓[/green] {display_msg} saved")
                    self.logged_outputs.add(log_key)
    
    def handle_tool_start(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """
        Handle tool start event - show tool execution start.
        
        Args:
            tool_name: Name of the tool being executed
            tool_input: Input parameters for the tool
        """
        if not tool_name:
            return  # Skip if no tool name
        
        # Extract skill_gap from input for course search
        skill_gap = ""
        if isinstance(tool_input, dict):
            skill_gap = tool_input.get("skill_gap", "")
        
        if tool_name == "search_learning_courses":
            skill_display = skill_gap if skill_gap else "learning opportunities"
            self.active_tools[tool_name] = True
            console.print(f"[cyan]🌐 Searching for courses: {skill_display}...[/cyan]")
        else:
            self.active_tools[tool_name] = True
            console.print(f"[cyan]🔧 Executing tool: {tool_name}...[/cyan]")
    
    def handle_tool_end(self, tool_name: str) -> None:
        """
        Handle tool end event - show tool completion.
        
        Args:
            tool_name: Name of the tool that completed
        """
        if not tool_name:
            return  # Skip if no tool name
        
        if tool_name in self.active_tools:
            self.active_tools[tool_name] = False
            if tool_name == "search_learning_courses":
                console.print(f"[green]✓[/green] Course search completed")
            else:
                console.print(f"[green]✓[/green] Tool {tool_name} completed")
    
    def handle_tool_error(self, tool_name: str, error: Any) -> None:
        """
        Handle tool error event - show tool errors.
        
        Args:
            tool_name: Name of the tool that errored
            error: Error information
        """
        if tool_name in self.active_tools:
            self.active_tools[tool_name] = False
            console.print(f"[red]❌ Tool error: {tool_name} - {str(error)[:100]}[/red]")
    
    def handle_node_error(self, node_name: str, error: Any) -> None:
        """
        Handle node error event - show node/chain errors.
        
        Args:
            node_name: Name of the node that errored
            error: Error information
        """
        matched_node = self._match_node_name(node_name)
        
        if matched_node:
            display_name = self.node_display_names[matched_node]
            console.print(f"[red]❌ {display_name} failed: {str(error)[:100]}[/red]")
            self.active_node = None
            self.generation_shown.discard(matched_node)
    
    def handle_state_update(self, state_update: Dict[str, Any]) -> None:
        """
        Handle graph-level state updates (fallback).
        
        Args:
            state_update: State update dictionary
        """
        if isinstance(state_update, dict):
            if self.final_state:
                self.final_state.update(state_update)
            else:
                self.final_state = state_update.copy()
    
    def get_final_state(self) -> Optional[Dict[str, Any]]:
        """
        Get the accumulated final state.
        
        Returns:
            Final state dictionary or None
        """
        return self.final_state
    

