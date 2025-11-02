"""Gap analyzer agent for identifying skill gaps."""
from typing import Dict, Any, Optional
import sys
from langchain_core.runnables import RunnableConfig
from google.api_core import exceptions as google_exceptions

from agents.base import BaseAgent
from orchestrator.state import State
from utils import truncate_input_dict


class GapAnalyzerAgent(BaseAgent):
    """Agent that identifies gaps between current capabilities and target requirements."""
    
    def __init__(self):
        super().__init__(
            name="gap_analyzer"
        )
    
    '''
        Add from Handbook.md
    '''
    
    def get_human_prompt_template(self) -> str:
        '''
        Add from Handbook.md
        '''
    
    def validate_state(self, state: State) -> Optional[Dict[str, Any]]:
        """Validate that competency_analyzer_output exists."""
        competency_output = state.get("competency_analyzer_output", "").strip()
        if not competency_output:
            return {
                "gap_analyzer_output": (
                    "Error: Competency analyzer output is missing. "
                    "Please run competency analysis first."
                )
            }
        return None
    
    def prepare_input(self, state: State) -> Dict[str, Any]:
        """Prepare input including competency output and performance evidence."""
        base_input = super().prepare_input(state)
        base_input.update({
            "competency_analyzer_output": state.get("competency_analyzer_output", ""),
            "manager_notes": state["data_files"].get("manager_notes", ""),
            "performance_reviews": state["data_files"].get("performance_reviews", ""),
            "peer_feedback": state["data_files"].get("peer_feedback", ""),
            "self_assessment": state["data_files"].get("self_assessment", ""),
            "project_contributions": state["data_files"].get("project_contributions", "")
        })
        return base_input
    
    def get_output_key(self) -> str:
        return "gap_analyzer_output"
    
    def execute(
        self,
        state: State,
        config: RunnableConfig | None = None
    ) -> Dict[str, Any]:
        """
        Execute gap analysis with input truncation and basic error handling.
        
        Overrides base execute to add input truncation for quota management.
        """
        # Validate state
        validation_error = self.validate_state(state)
        if validation_error:
            return validation_error
        
        try:
            # Create LLM and prompt
            llm = self.create_llm()
            prompt = self.create_prompt()
            chain = prompt | llm
            
            # Prepare input data
            input_data = self.prepare_input(state)
            
            # Truncate inputs to prevent quota exhaustion
            # Gap analyzer uses the most data (5 files + competency output)
            # Limit each field to 6000 chars (~1500 tokens) per field
            input_data = truncate_input_dict(input_data, max_chars_per_field=6000)
            
            # Use invoke() to call the chain (progress shown via LangGraph events)
            response = chain.invoke(input_data)
            
            # Extract content
            content = self.extract_response_content(response)
            
            if not content or not content.strip():
                error_msg = (
                    "Gap analysis could not be generated. "
                    "The LLM returned an empty response. "
                    "Please check your GEMINI_API_KEY and try again."
                )
                print(f"[WARNING] {error_msg}", file=sys.stderr)
                return {
                    "gap_analyzer_output": error_msg
                }
            
            return {self.get_output_key(): content}
        
        except google_exceptions.ResourceExhausted as e:
            error_msg = (
                "Gap analysis failed due to API quota limit exceeded. "
                "The Gemini API daily input token quota (250,000 tokens) has been reached. "
                "Input data has been truncated. Please try again later or reduce data file sizes."
            )
            print(f"[ERROR] ResourceExhausted: {str(e)[:200]}", file=sys.stderr)
            return {
                "gap_analyzer_output": error_msg
            }
        
        except ValueError as e:
            # Handle "No generations found in stream" error
            error_str = str(e)
            if "No generations found" in error_str:
                error_msg = (
                    "Gap analysis generation encountered an issue. "
                    "The LLM did not return a response. "
                    "This may be due to API quota limits, content filtering, or network issues. "
                    "Input data has been truncated. Please check your GEMINI_API_KEY and try again."
                )
                return {
                    "gap_analyzer_output": error_msg
                }
            # Re-raise other ValueErrors
            raise
        
        except Exception as e:
            # Catch any other exceptions and provide helpful error message
            error_type = type(e).__name__
            error_str = str(e)[:200]
            
            # Check if it's quota-related
            if "quota" in error_str.lower() or "429" in error_str or "ResourceExhausted" in error_str:
                error_msg = (
                    "Gap analysis failed due to API quota limit. "
                    "Input data has been truncated. Please try again later."
                )
            else:
                error_msg = (
                    f"Gap analysis generation failed with error: {error_type}: {error_str}. "
                    "Please check your GEMINI_API_KEY and network connection."
                )
            print(f"[ERROR] {error_type}: {error_str}", file=sys.stderr)
            
            return {
                "gap_analyzer_output": error_msg
            }


def gap_analyzer_node(
    state: Dict[str, Any],
    config: RunnableConfig | None = None
) -> Dict[str, Any]:
    """
    Node function for LangGraph compatibility.
    
    Args:
        state: Current workflow state
        config: RunnableConfig for streaming
    
    Returns:
        Dictionary with gap_analyzer_output
    """
    agent = GapAnalyzerAgent()
    return agent.execute(state, config)

