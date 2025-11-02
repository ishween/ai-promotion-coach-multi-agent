"""LangGraph-specific adapter for converting events to abstract handler calls."""
from typing import Dict, Any
import json

from orchestrator.streaming_handler import StreamingHandler


class LangGraphStreamAdapter:
    """
    Adapter that converts LangGraph events to abstract StreamingHandler calls.
    
    This class isolates LangGraph-specific event structure and naming from
    the business logic in StreamingHandler. If LangGraph changes its event
    format, only this adapter needs to be updated.
    """
    
    def __init__(self, handler: StreamingHandler, debug: bool = False):
        """
        Initialize adapter with a streaming handler.
        
        Args:
            handler: StreamingHandler instance to delegate to
            debug: If True, log event structures for debugging
        """
        self.handler = handler
        self.tool_events_captured = []  # For verification
        self.debug = debug
    
    def process_event(self, event: Dict[str, Any]) -> None:
        """
        Convert LangGraph event to handler call.
        
        This method extracts data from LangGraph's event structure and calls
        the appropriate handler method, which contains pure business logic.
        
        Args:
            event: LangGraph event dictionary with structure:
                  {
                      "event": "on_chain_start" | "on_tool_start" | etc.,
                      "name": "node_name",
                      "data": {...}
                  }
        """
        event_name = event.get("event", "")
        
        if event_name == "on_chain_start":
            node_name = event.get("name", "")
            self.handler.handle_node_start(node_name)
        
        elif event_name == "on_chat_model_stream":
            node_name = event.get("name", "")
            self.handler.handle_node_generating(node_name)
        
        elif event_name == "on_chain_end":
            node_name = event.get("name", "")
            event_data = event.get("data", {})
            output = event_data.get("output", {})
            self.handler.handle_node_end(node_name, output)
        
        elif event_name == "on_tool_start":
            event_data = event.get("data", {})
            
            # Debug: Log event structure if enabled
            if self.debug:
                from rich.console import Console
                console = Console()
                console.print(f"[dim]🔍 DEBUG on_tool_start event structure:[/dim]")
                console.print(f"[dim]  event.name: {event.get('name', 'N/A')}[/dim]")
                console.print(f"[dim]  event.data keys: {list(event_data.keys()) if isinstance(event_data, dict) else 'N/A'}[/dim]")
                if isinstance(event_data, dict):
                    console.print(f"[dim]  event.data: {json.dumps(event_data, indent=2, default=str)[:500]}[/dim]")
            
            # Extract tool name and input from LangGraph event
            tool_name = self._extract_tool_name(event)
            tool_input = event_data.get("input", {}) if isinstance(event_data, dict) else {}
            
            # Track for verification
            self.tool_events_captured.append(("start", tool_name))
            
            # Call handler - this displays the progress (console.print inside handler)
            self.handler.handle_tool_start(tool_name, tool_input)
        
        elif event_name == "on_tool_end":
            # Extract tool name from LangGraph event
            tool_name = self._extract_tool_name(event)
            
            # Track for verification
            self.tool_events_captured.append(("end", tool_name))
            
            # Call handler - this displays the completion (console.print inside handler)
            self.handler.handle_tool_end(tool_name)
        
        elif event_name == "on_tool_error":
            # Extract tool name and error from LangGraph event
            tool_name = self._extract_tool_name(event)
            event_data = event.get("data", {})
            error = event_data.get("error", "") if isinstance(event_data, dict) else ""
            
            self.handler.handle_tool_error(tool_name, error)
        
        elif event_name == "on_chain_error":
            node_name = event.get("name", "")
            event_data = event.get("data", {})
            error = event_data.get("error", "")
            self.handler.handle_node_error(node_name, error)
        
        elif event_name == "on_graph_update":
            # Handle graph-level state updates (fallback)
            event_data = event.get("data", {})
            state_update = event_data
            self.handler.handle_state_update(state_update)
    
    def _extract_tool_name(self, event: Dict[str, Any]) -> str:
        """
        Extract tool name from LangGraph event.
        
        LangGraph emits tool names in event["name"] field, either:
        - Directly: "search_learning_courses"
        - Prefixed: "tools.search_learning_courses"
        
        Args:
            event: LangGraph event dictionary
        
        Returns:
            Tool name string, or empty string if not found
        """
        event_name_field = event.get("name", "")
        
        if not event_name_field or event_name_field == "tools":
            return ""
        
        # Handle both formats: "search_learning_courses" or "tools.search_learning_courses"
        if "." in event_name_field:
            parts = event_name_field.split(".")
            return parts[-1] if len(parts) > 1 else ""
        
        return event_name_field
    
    def get_tool_events_captured(self) -> list:
        """
        Get list of captured tool events for verification.
        
        Returns:
            List of tuples (event_type, tool_name)
        """
        return self.tool_events_captured

