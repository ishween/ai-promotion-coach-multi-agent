"""Base agent class for promotion coach agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from utils import create_llm
from orchestrator.state import State


class BaseAgent(ABC):
    """
    Abstract base class for all promotion coach agents.
    
    Provides common functionality for LLM interaction, streaming,
    prompt creation, and error handling. Subclasses implement
    agent-specific prompts and business logic.
    """
    
    def __init__(
        self,
        name: str,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.7
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent identifier (used for logging and status messages)
            model_name: LLM model name to use
            temperature: LLM temperature setting
        """
        self.name = name
        self.model_name = model_name
        self.temperature = temperature
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Returns:
            System prompt string describing the agent's role and behavior
        """
        pass
    
    @abstractmethod
    def get_human_prompt_template(self) -> str:
        """
        Get the human prompt template with placeholders.
        
        Returns:
            Human prompt template string with {placeholders}
        """
        pass
    
    def create_prompt(self) -> ChatPromptTemplate:
        """
        Create LangChain prompt template from system and human prompts.
        
        Returns:
            ChatPromptTemplate instance
        """
        return ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("human", self.get_human_prompt_template())
        ])
    
    def create_llm(self):
        """
        Create LLM instance with agent's configuration.
        
        Returns:
            LLM instance configured with model_name and temperature
        """
        return create_llm(model_name=self.model_name, temperature=self.temperature)
    
    def extract_response_content(self, response: Any) -> str:
        """
        Extract content from LLM response with fallback handling.
        
        Args:
            response: LLM response object
        
        Returns:
            Response content as string
        
        Raises:
            ValueError: If content cannot be extracted
        """
        if hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'text'):
            return response.text
        elif isinstance(response, str):
            return response
        else:
            # Try string representation as last resort
            content = str(response)
            if not content or not content.strip():
                raise ValueError(
                    f"Could not extract content from response. "
                    f"Response type: {type(response).__name__}"
                )
            return content
    
    def validate_state(self, state: State) -> Optional[Dict[str, Any]]:
        """
        Validate state before processing.
        
        Override in subclasses to add state validation.
        Returns error dict if validation fails, None if valid.
        
        Args:
            state: Workflow state
        
        Returns:
            Error dictionary with error message, or None if valid
        """
        return None
    
    def execute(
        self,
        state: State,
        config: RunnableConfig | None = None
    ) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        
        This is the template method that orchestrates the agent execution.
        Progress is shown via LangGraph's native events (on_chain_start, on_chat_model_stream, on_chain_end).
        Subclasses can override specific steps if needed.
        
        Args:
            state: Current workflow state
            config: RunnableConfig (not used for streaming anymore, kept for compatibility)
        
        Returns:
            Dictionary with agent output (e.g., {"competency_analyzer_output": "..."})
        """
        # Validate state
        validation_error = self.validate_state(state)
        if validation_error:
            return validation_error
        
        # Create LLM and prompt
        llm = self.create_llm()
        prompt = self.create_prompt()
        chain = prompt | llm
        
        # Prepare input data (override prepare_input in subclasses if needed)
        input_data = self.prepare_input(state)
        
        # Invoke chain (progress shown via LangGraph events)
        response = chain.invoke(input_data)
        
        # Extract content
        content = self.extract_response_content(response)
        
        # Return output (override get_output_key in subclasses)
        return {self.get_output_key(): content}
    
    def prepare_input(self, state: State) -> Dict[str, Any]:
        """
        Prepare input data for prompt from state.
        
        Override in subclasses to customize input preparation.
        
        Args:
            state: Current workflow state
        
        Returns:
            Dictionary of input variables for prompt template
        """
        return {
            "name": state["name"],
            "current_level": state["current_level"],
            "target_level": state["target_level"],
            "discipline": state["discipline"]
        }
    
    @abstractmethod
    def get_output_key(self) -> str:
        """
        Get the state key for storing this agent's output.
        
        Returns:
            State key string (e.g., "competency_analyzer_output")
        """
        pass

