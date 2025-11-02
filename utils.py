"""Utility functions for file reading and state management."""
import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from rich.console import Console
from rich.table import Table

console = Console()

DATA_FOLDER = Path(__file__).parent / "data"
OUTPUTS_FOLDER = Path(__file__).parent / "outputs"


def create_llm(model_name: str = "gemini-2.5-flash", temperature: float = 0.7):
    """
    Create a LangChain LLM instance using Google Gemini.
    
    This is the centralized function for creating LLM instances across the application.
    All nodes and agents should use this function for consistency.
    
    Args:
        model_name: The Gemini model name to use (default: "gemini-2.5-flash")
        temperature: Temperature for generation, between 0.0 and 2.0 (default: 0.7)
    
    Returns:
        ChatGoogleGenerativeAI instance configured with the specified parameters
    
    Raises:
        ValueError: If GEMINI_API_KEY is not found in environment variables
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key
        # max_output_tokens removed - using model default (typically 8192+ for gemini-2.5-flash)
        # The model default is sufficient for complete responses
    )


def truncate_text(text: str, max_chars: int = 8000, preserve_end: bool = True) -> str:
    """
    Truncate text to prevent excessive token usage.
    
    Args:
        text: Text to truncate
        max_chars: Maximum characters (roughly 2000 tokens at 4 chars/token)
        preserve_end: If True, keep the end of text; if False, keep the beginning
    
    Returns:
        Truncated text with note if truncated
    """
    if not text or len(text) <= max_chars:
        return text
    
    if preserve_end:
        # Keep the end (more recent/important info)
        truncated = text[-max_chars:]
        note = f"\n\n[Note: Previous content truncated to {max_chars} chars for token conservation - showing most recent content]"
    else:
        # Keep the beginning
        truncated = text[:max_chars]
        note = f"\n\n[Note: Remaining content truncated to {max_chars} chars for token conservation]"
    
    return truncated + note


def truncate_input_dict(input_data: Dict[str, Any], max_chars_per_field: int = 8000) -> Dict[str, Any]:
    """
    Truncate string values in input dictionary to prevent quota exhaustion.
    
    Args:
        input_data: Dictionary of input variables for prompt
        max_chars_per_field: Maximum characters per field (~2000 tokens at 4 chars/token)
    
    Returns:
        Dictionary with truncated string values
    """
    truncated = {}
    for key, value in input_data.items():
        if isinstance(value, str):
            truncated[key] = truncate_text(value, max_chars_per_field, preserve_end=True)
        else:
            truncated[key] = value
    return truncated


def read_data_files() -> Dict[str, str]:
    """Read all txt files from the data folder."""
    data_files = {
        "company_leveling_document": "company_leveling_document.txt",
        "project_contributions": "project_contributions.txt",
        "manager_notes": "manager_notes.txt",
        "performance_reviews": "performance_reviews.txt",
        "peer_feedback": "peer_feedback.txt",
        "self_assessment": "self_assessment.txt",
        "project_pipeline": "project_pipeline.txt",
        "company_initiatives": "company_initiatives.txt",
        "team_roadmap": "team_roadmap.txt",
    }
    
    result = {}
    for key, filename in data_files.items():
        file_path = DATA_FOLDER / filename
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                result[key] = f.read()
        else:
            result[key] = ""
            console.print(f"[yellow]Warning: {filename} not found[/yellow]")
    
    return result


def markdown_to_html(markdown_text: str) -> str:
    """Simple markdown to HTML converter for basic formatting."""
    import re
    
    html = markdown_text
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Lists
    lines = html.split('\n')
    in_list = False
    result_lines = []
    
    for line in lines:
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            item = line.strip()[2:]
            result_lines.append(f'<li>{item}</li>')
        elif re.match(r'^\d+\.\s+', line.strip()):
            if not in_list:
                result_lines.append('<ol>')
                in_list = True
            item = re.sub(r'^\d+\.\s+', '', line.strip())
            result_lines.append(f'<li>{item}</li>')
        else:
            if in_list:
                if result_lines and result_lines[-1].startswith('<li>'):
                    result_lines.append('</ul>' if result_lines[-2].startswith('<ul>') else '</ol>')
                in_list = False
            if line.strip() and not line.strip().startswith('<'):
                result_lines.append(f'<p>{line}</p>')
            else:
                result_lines.append(line)
    
    if in_list:
        result_lines.append('</ul>')
    
    html = '\n'.join(result_lines)
    
    # Links
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
    
    # Code blocks
    html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    
    # Inline code
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    
    return html


def generate_html_report(name: str, output_type: str, content: str, timestamp: str) -> str:
    """Generate a styled HTML report."""
    # Convert markdown to HTML (simple conversion for basic markdown)
    html_body = markdown_to_html(content)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{output_type.replace('_', ' ').title()} - {name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-top: 30px;
            margin-bottom: 25px;
            font-size: 2em;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.6em;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }}
        
        h3 {{
            color: #555;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        
        ul, ol {{
            margin-left: 30px;
            margin-bottom: 20px;
        }}
        
        li {{
            margin-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        code {{
            background-color: #f4f4f4;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        pre {{
            background-color: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        
        blockquote {{
            border-left: 4px solid #667eea;
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #555;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        strong {{
            color: #667eea;
            font-weight: 600;
        }}
        
        a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{output_type.replace('_', ' ').title()}</h1>
            <p>Engineer: {name} | Generated: {timestamp}</p>
        </div>
        <div class="content">
            {html_body}
        </div>
        <div class="footer">
            <p>Generated by Promotion Coach System</p>
        </div>
    </div>
</body>
</html>"""


def generate_combined_html_report(name: str, outputs: Dict[str, str]) -> str:
    """Generate a combined HTML report with all outputs in tabs."""
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    sections = []
    tabs = []
    
    section_order = [
        ("competency_analyzer", "Competency Analysis"),
        ("gap_analyzer", "Gap Analysis"),
        ("opportunity_finder", "Opportunity Finder"),
        ("promotion_package", "Promotion Package")
    ]
    
    for idx, (key, title) in enumerate(section_order):
        if outputs.get(key) and outputs[key].strip():
            content_html = markdown_to_html(outputs[key])
            active = 'active' if idx == 0 else ''
            tabs.append(f'<button class="tab-button {active}" onclick="showTab({idx})">{title}</button>')
            sections.append(f'''
                <div id="tab-{idx}" class="tab-content {'active' if idx == 0 else ''}">
                    <h1>{title}</h1>
                    {content_html}
                </div>
            ''')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Promotion Coach Report - {name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .tabs {{
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #e0e0e0;
            overflow-x: auto;
        }}
        
        .tab-button {{
            flex: 1;
            padding: 20px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 500;
            color: #666;
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }}
        
        .tab-button:hover {{
            background: #e9ecef;
            color: #667eea;
        }}
        
        .tab-button.active {{
            color: #667eea;
            border-bottom-color: #667eea;
            background: white;
        }}
        
        .content-area {{
            padding: 40px;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        h1 {{ color: #2c3e50; border-bottom: 3px solid #667eea; padding-bottom: 15px; margin-top: 20px; margin-bottom: 25px; }}
        h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 20px; border-left: 4px solid #667eea; padding-left: 15px; }}
        h3 {{ color: #555; margin-top: 25px; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #e0e0e0; }}
        tr:hover {{ background-color: #f8f9fa; }}
        code {{ background: #f4f4f4; padding: 3px 8px; border-radius: 4px; }}
        pre {{ background: #2d2d2d; color: #f8f8f2; padding: 20px; border-radius: 8px; overflow-x: auto; }}
        strong {{ color: #667eea; }}
        ul, ol {{ margin-left: 30px; margin-bottom: 20px; }}
        li {{ margin-bottom: 10px; }}
        p {{ margin-bottom: 15px; }}
    </style>
    <script>
        function showTab(index) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab-button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById('tab-' + index).classList.add('active');
            document.querySelectorAll('.tab-button')[index].classList.add('active');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Promotion Coach Analysis Report</h1>
            <p>Engineer: {name} | Generated: {timestamp}</p>
        </div>
        <div class="tabs">
            {''.join(tabs)}
        </div>
        <div class="content-area">
            {''.join(sections)}
        </div>
    </div>
</body>
</html>"""


def save_output(name: str, output_type: str, content: str) -> None:
    """Save output to JSON, Markdown, and HTML formats."""
    from datetime import datetime
    
    OUTPUTS_FOLDER.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save JSON version (for programmatic access)
    json_path = OUTPUTS_FOLDER / f"{name}_{output_type}.json"
    data = {
        "name": name,
        "output_type": output_type,
        "content": content,
        "generated_at": datetime.now().isoformat()
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Save HTML version (for demo/sharing)
    html_path = OUTPUTS_FOLDER / f"{name}_{output_type}.html"
    html_content = generate_html_report(name, output_type, content, timestamp)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Save Markdown version (optional, for GitHub/docs)
    md_path = OUTPUTS_FOLDER / f"{name}_{output_type}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {output_type.replace('_', ' ').title()} - {name}\n\n")
        f.write(f"**Generated:** {timestamp}\n\n---\n\n{content}")


def load_output(name: str, output_type: str) -> Optional[str]:
    """Load previous output if it exists."""
    file_path = OUTPUTS_FOLDER / f"{name}_{output_type}.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("content", "")
    return None


def load_all_outputs(name: str) -> Dict[str, Optional[str]]:
    """Load all previous outputs for a given name."""
    outputs = {
        "competency_analyzer": load_output(name, "competency_analyzer"),
        "gap_analyzer": load_output(name, "gap_analyzer"),
        "opportunity_finder": load_output(name, "opportunity_finder"),
        "promotion_package": load_output(name, "promotion_package"),
    }
    return outputs


def has_previous_outputs(name: str) -> bool:
    """Check if there are any previous outputs."""
    outputs = load_all_outputs(name)
    return any(output is not None for output in outputs.values())


def display_output_table(outputs: Dict[str, Optional[str]]) -> Table:
    """Display outputs in a nice table format."""
    table = Table(title="Analysis Outputs", show_header=True, header_style="bold magenta")
    table.add_column("Output Type", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Preview", style="dim")
    
    for output_type, content in outputs.items():
        status = "✓ Available" if content else "✗ Not Available"
        preview = content[:100] + "..." if content and len(content) > 100 else (content or "N/A")
        table.add_row(output_type.replace("_", " ").title(), status, preview)
    
    return table


def update_data_file(filename: str, content: str) -> None:
    """Update a data file with new content."""
    file_path = DATA_FOLDER / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def prompt_for_additional_info(data_files: Dict[str, str]) -> Dict[str, str]:
    """Prompt user to provide additional information for each data file."""
    console.print("\n[bold cyan]Please provide additional information for each data file:[/bold cyan]\n")
    
    updated_files = {}
    file_mapping = {
        "project_contributions": "project_contributions.txt",
        "manager_notes": "manager_notes.txt",
        "performance_reviews": "performance_reviews.txt",
        "peer_feedback": "peer_feedback.txt",
        "self_assessment": "self_assessment.txt",
        "project_pipeline": "project_pipeline.txt",
        "company_initiatives": "company_initiatives.txt",
        "team_roadmap": "team_roadmap.txt",
    }
    
    for key, filename in file_mapping.items():
        current_content = data_files.get(key, "")
        console.print(f"\n[bold yellow]{filename}[/bold yellow]")
        if current_content:
            console.print(f"[dim]Current content (first 200 chars): {current_content[:200]}...[/dim]")
        
        console.print(f"[cyan]Enter additional information for {filename} (press Enter twice to finish, 'skip' to keep current):[/cyan]")
        
        lines = []
        while True:
            line = input()
            if line.strip().lower() == "skip":
                updated_files[key] = current_content
                break
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        
        if line.strip().lower() != "skip":
            new_content = "\n".join(lines[:-1])  # Remove last empty line
            if current_content:
                updated_files[key] = current_content + "\n\n" + new_content
            else:
                updated_files[key] = new_content
    
    return updated_files

