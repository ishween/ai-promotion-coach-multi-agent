# Hands-on Guide #

## State (orchestrator/state.py) ##
```
competency_analyzer_output: str
gap_analyzer_output: str
opportunity_finder_output: Annotated[str, reduce_opportunity_output]
promotion_package_output: str
```

## Graph Setup (orchestrator/graph.py) ##
### Nodes ###
* `workflow.add_node("gap_analyzer", gap_analyzer_node)`
* `workflow.add_node("promotion_package", promotion_package_node)`
* `workflow.add_node("human_review", human_review_node)`

### Edges ###
#### Parallel Edges ####
`workflow.add_edge("competency_analyzer", "gap_analyzer")` <br>
`workflow.add_edge("competency_analyzer", "promotion_package")`

#### Conditional Edges ####
```
workflow.add_conditional_edges(
  "opportunity_finder",
  should_call_tools,
  {
    ROUTE_TOOLS: "tools",
    ROUTE_HUMAN_REVIEW: "human_review"
  }
)
```
##### Routing for conditional edge (orchestrator/routing.py) #####
```
def should_call_tools(state: State) -> Literal["tools", "human_review"]:
    """
    Check if we need to call tools after opportunity finder.
    
    Decision logic:
    - If messages contain tool_calls: Route to tools
    - If opportunity_finder_output is empty but messages exist: Route to tools
    - Otherwise: Route to human_review
    
    Args:
        state: Current workflow state
    
    Returns:
        Route name: "tools" or "human_review"
    """
    messages = state.get("messages", [])
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            return ROUTE_TOOLS
    
    if not state.get("opportunity_finder_output") and messages:
        return ROUTE_TOOLS
    
    return ROUTE_HUMAN_REVIEW
```

#### Graph Compile ####
`app = workflow.compile(checkpointer=memory)`

## LLM ##
```
def create_llm(model_name: str = "gemini-2.5-flash", temperature: float = 0.7):
    
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key
    )
```

## Agents ##
### Competency Analyzer ###
```
chain = prompt | llm
```

```
response = chain.invoke(input_data)
```

```
return {self.get_output_key(): content}
```

### Gap Analyzer ###
```
def get_system_prompt(self) -> str:
        return """You are a Career Gap Analysis Specialist who specializes in gap analysis. 
        You carefully compare engineers' current performance, skills, and achievements against 
        target-level requirements. You identify specific areas for development and prioritize 
        them based on impact and feasibility.
        
        Your goal is to identify gaps between an engineer's current capabilities and target 
        promotion level requirements."""
```

```
def get_human_prompt_template(self) -> str:
        return """Identify gaps between {name}'s current capabilities and target level requirements.

CONTEXT:
- Engineer: {name}
- Current Level: {current_level}
- Target Level: {target_level}
- Discipline: {discipline}

COMPETENCY REQUIREMENTS:
{competency_analyzer_output}

PERFORMANCE EVIDENCE:
- Manager Notes: {manager_notes}
- Performance Reviews: {performance_reviews}
- Peer Feedback: {peer_feedback}
- Self Assessment: {self_assessment}
- Project Contributions: {project_contributions}

YOUR TASK:
1. Compare current capabilities against target requirements
2. Identify specific gaps in skills, experience, and behaviors
3. Prioritize gaps based on impact and feasibility
4. Provide actionable recommendations

OUTPUT FORMAT:
Structured analysis with:
- Identified gaps
- Priority levels
- Evidence assessment
- Development recommendations"""
```

### Opportunity Finder ###
```
if wants_course_suggestions:
  tools = [search_learning_courses]
  llm_with_tools = llm.bind_tools(tools)
else:
  llm_with_tools = llm
```

### Promotion Package ###
```
def promotion_package_node(
    state: Dict[str, Any],
    config: RunnableConfig | None = None
) -> Dict[str, Any]:
    """
    Node function for LangGraph compatibility.
    
    Args:
        state: Current workflow state
        config: RunnableConfig (not used, but required for signature)
    
    Returns:
        Dictionary with promotion_package_output
    """
    agent = PromotionPackageAgent()
    return agent.execute(state, config)
```

## Tools ##
### search_learning_courses (tools/course_search.py) ###
`@tool`

```
serper_url = "https://google.serper.dev/search"
headers = {
  "X-API-KEY": SERPER_API_KEY,
  "Content-Type": "application/json"
}
```

### process tools (orchestrator/tools.py) ###
```
llm = create_llm()
final_messages = [
  SystemMessage(content="You are a Career Opportunity Strategist."),
  HumanMessage(content=f"Gap Analysis:\n{gap_analysis}\n\nProvide opportunity recommendations."),
]
response = llm.invoke(final_messages)
```

## Streaming (orchestrator/workflow.py) ##
```
async for event in app.astream_events(
        initial_state,
        config=config,
        version="v2"
    ):
```


`
