"""Competency analyzer agent for analyzing promotion requirements."""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from agents.base import BaseAgent
from orchestrator.state import State


class CompetencyAnalyzerAgent(BaseAgent):
    """Agent that analyzes competency requirements for target promotion level."""
    
    def __init__(self):
        super().__init__(
            name="competency_analyzer"
        )
    
    def get_system_prompt(self) -> str:
        return """You are a Senior Engineering Competency Analyst with years of experience 
        helping engineers understand what it takes to advance in their careers. You excel at 
        parsing company leveling documents and translating them into actionable competency frameworks.
        
        Your goal is to analyze and define specific competency requirements for an engineer's 
        target promotion level based on company leveling documents."""
    
    def get_human_prompt_template(self) -> str:
        return """Analyze the competency requirements for promotion from {current_level} to {target_level} in {discipline}.

CONTEXT:
- Engineer Name: {name}
- Current Level: {current_level}
- Target Level: {target_level}
- Discipline: {discipline}

COMPANY LEVELING DOCUMENT:
{company_leveling_document}

YOUR TASK:
1. Parse and interpret the company leveling document
2. Identify technical, leadership, and soft skill requirements for the target level
3. Map discipline-specific expectations
4. Generate a comprehensive competency framework

OUTPUT FORMAT:
Provide a structured JSON response with:
- target_level
- current_level
- discipline
- competency_categories (with requirements, importance, evaluation_criteria)
- level_differentiators
- expected_scope
- expected_impact

Be professional, objective, and encouraging."""
    
    def prepare_input(self, state: State) -> Dict[str, Any]:
        """Prepare input including company leveling document."""
        base_input = super().prepare_input(state)
        base_input["company_leveling_document"] = state["data_files"]["company_leveling_document"]
        return base_input
    
    def get_output_key(self) -> str:
        return "competency_analyzer_output"
    
    def execute(
        self,
        state: State,
        config: RunnableConfig | None = None
    ) -> Dict[str, Any]:
        """
        Execute competency analysis.
        
        Progress is shown via LangGraph's native events.
        """
        # Validate state
        validation_error = self.validate_state(state)
        if validation_error:
            return validation_error
        
        # Create LLM and prompt
        llm = self.create_llm()
        prompt = self.create_prompt()
        
        '''
        Add from Handbook.md
        '''
        
        # Prepare input data
        input_data = self.prepare_input(state)
        
        # Invoke chain (progress shown via LangGraph events)
        '''
        Add from Handbook.md
        '''       
        
        # Extract content
        content = self.extract_response_content(response)
        
        '''
        Add from Handbook.md
        '''


def competency_analyzer_node(
    state: Dict[str, Any],
    config: RunnableConfig | None = None
) -> Dict[str, Any]:
    """
    Node function for LangGraph compatibility.
    
    Args:
        state: Current workflow state
        config: RunnableConfig for streaming
    
    Returns:
        Dictionary with competency_analyzer_output
    """
    agent = CompetencyAnalyzerAgent()
    return agent.execute(state, config)

