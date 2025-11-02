"""Promotion package agent for creating promotion documents."""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from agents.base import BaseAgent
from orchestrator.state import State


class PromotionPackageAgent(BaseAgent):
    """Agent that creates promotion package documents."""
    
    def __init__(self):
        super().__init__(
            name="promotion_package"
        )
    
    def get_system_prompt(self) -> str:
        return """You are an expert at crafting promotion packages that highlight engineers' 
        accomplishments in a compelling way. You use evidence-based writing, professional tone, 
        and impactful language. You ensure all claims are backed by actual data and never 
        exaggerate achievements.
        
        Your goal is to create honest, professional, and impactful promotion packages that 
        accurately represent an engineer's achievements."""
    
    def get_human_prompt_template(self) -> str:
        return """Create a promotion package for {name} from {current_level} to {target_level}.

CONTEXT:
- Engineer: {name}
- Current Level: {current_level}
- Target Level: {target_level}
- Discipline: {discipline}

EVIDENCE SOURCES:
- Project Contributions: {project_contributions}
- Manager Notes: {manager_notes}
- Performance Reviews: {performance_reviews}
- Peer Feedback: {peer_feedback}
- Self Assessment: {self_assessment}

COMPETENCY REQUIREMENTS:
{competency_analyzer_output}

YOUR TASK:
1. Create executive summary highlighting key achievements
2. Document specific accomplishments with evidence
3. Map contributions to target-level competencies
4. Include stakeholder feedback
5. Identify growth areas and recommendations

OUTPUT FORMAT:
Professional promotion package with:
- Executive summary
- Key accomplishments
- Competency evidence
- Project contributions
- Stakeholder feedback
- Growth areas
- Recommendations

Use professional, impactful language. Be honest and evidence-based. Never exaggerate."""
    
    def prepare_input(self, state: State) -> Dict[str, Any]:
        """Prepare input including all evidence sources and competency output."""
        base_input = super().prepare_input(state)
        base_input.update({
            "project_contributions": state["data_files"]["project_contributions"],
            "manager_notes": state["data_files"]["manager_notes"],
            "performance_reviews": state["data_files"]["performance_reviews"],
            "peer_feedback": state["data_files"]["peer_feedback"],
            "self_assessment": state["data_files"]["self_assessment"],
            "competency_analyzer_output": state.get("competency_analyzer_output", "")
        })
        return base_input
    
    def get_output_key(self) -> str:
        return "promotion_package_output"
    
    def execute(
        self,
        state: State,
        config: RunnableConfig | None = None
    ) -> Dict[str, Any]:
        """
        Execute promotion package creation.
        
        Progress is shown via LangGraph's native events.
        """
        # Validate state
        validation_error = self.validate_state(state)
        if validation_error:
            return validation_error
        
        # Create LLM and prompt
        llm = self.create_llm()
        prompt = self.create_prompt()
        chain = prompt | llm
        
        # Prepare input data
        input_data = self.prepare_input(state)
        
        # Invoke chain (progress shown via LangGraph events)
        response = chain.invoke(input_data)
        
        # Extract content
        content = self.extract_response_content(response)
        
        return {self.get_output_key(): content}


        '''
        Add from Handbook.md
        '''

