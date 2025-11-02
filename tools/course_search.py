"""Tool for searching learning courses using Serper API and web scraping."""
import json
import os
from typing import Dict, List, Any
from langchain_core.tools import tool
from langchain_core.tools import ToolException
import requests
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if not SERPER_API_KEY:
    raise ValueError("SERPER_API_KEY not found in environment variables")

# @tool is used to convert the function to a tool that can be used in the workflow
@tool
def search_learning_courses(
    skill_gap: str,
    learning_style: str = "online",
    max_results: int = 3
) -> str:
    """
    Search for learning courses that match the given skill gap and learning style using Serper API.
    
    Args:
        skill_gap: The specific skill gap that needs to be addressed
        learning_style: Preferred learning style (online, in-person, hybrid)
        max_results: Maximum number of courses to return
    
    Returns:
        JSON string containing course information with name, provider, link, price, duration, and rating
    """
    try:
        # Build search query
        query = f"{skill_gap} course {learning_style} learning"
        
        # Search using Serper API
        serper_url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        # Cap max_results at 3
        max_results = min(max_results, 3)
        
        payload = {
            "q": query,
            "num": max_results * 2,  # Get more results to filter better
            "gl": "us",
            "hl": "en"
        }
        
        response = requests.post(serper_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        search_results = response.json()
        
        courses = []
        
        # Extract organic results
        organic_results = search_results.get("organic", [])
        
        # Process each result
        for result in organic_results[:max_results * 2]:
            title = result.get("title", "")
            link = result.get("link", "")
            snippet = result.get("snippet", "")
            
            # Filter for course-related results
            course_keywords = ["course", "learn", "training", "tutorial", "class", "education"]
            if any(keyword in title.lower() or keyword in snippet.lower() for keyword in course_keywords):
                # Scrape additional details from the page
                course_info = scrape_course_details(link, title, snippet)
                if course_info:
                    courses.append(course_info)
                    if len(courses) >= max_results:
                        break
        
        # Limit results to max_results (don't try to find more if we have fewer)
        courses = courses[:max_results]
        
        # If no results at all, create a placeholder (only if completely empty)
        if len(courses) == 0:
            courses = [{
                "name": f"Learning Resources for {skill_gap}",
                "provider": "Various Platforms",
                "link": f"https://www.google.com/search?q={skill_gap.replace(' ', '+')}+course",
                "price": "Varies",
                "duration": "Varies",
                "rating": "N/A",
                "description": f"Search for {skill_gap} courses on online learning platforms"
            }]
        
        result = {
            "skill_gap": skill_gap,
            "learning_style": learning_style,
            "courses_found": len(courses),
            "courses": courses
        }
        
        return json.dumps(result, indent=2)
    
    except requests.exceptions.RequestException as e:
        raise ToolException(f"Error calling Serper API: {str(e)}")
    except Exception as e:
        raise ToolException(f"Error searching for courses: {str(e)}")


def scrape_course_details(url: str, title: str, snippet: str) -> Dict[str, Any] | None:
    """
    Extract course details from URL and search snippet.
    
    Simplified version that only extracts reliably available information:
    - Provider name from URL domain
    - Description from search snippet
    - Basic course info without unreliable web scraping
    
    Args:
        url: URL of the course page
        title: Title from search results
        snippet: Snippet from search results
    
    Returns:
        Dictionary with course information or None if extraction fails
    """
    try:
        # Determine provider from URL domain (most reliable)
        provider = "Unknown"
        url_lower = url.lower()
        if "coursera.org" in url_lower:
            provider = "Coursera"
        elif "udemy.com" in url_lower:
            provider = "Udemy"
        elif "edx.org" in url_lower:
            provider = "edX"
        elif "pluralsight.com" in url_lower:
            provider = "Pluralsight"
        elif "linkedin.com" in url_lower or "lynda.com" in url_lower:
            provider = "LinkedIn Learning"
        elif "khanacademy.org" in url_lower:
            provider = "Khan Academy"
        elif "codecademy.com" in url_lower:
            provider = "Codecademy"
        
        # Use snippet as description (most reliable source)
        description = snippet.strip() if snippet else f"Course available on {provider}"
        
        # Limit description length
        if len(description) > 300:
            description = description[:297] + "..."
        
        return {
            "name": title,
            "provider": provider,
            "link": url,
            "price": "Varies",  # Most courses have dynamic pricing, not reliable to scrape
            "duration": "Varies",  # Course duration often requires account access
            "rating": "N/A",  # Ratings require login/API access for most platforms
            "description": description
        }
    
    except Exception:
        return None


def verify_course_fit(
    course_info: Dict[str, Any],
    criteria: str
) -> Dict[str, Any]:
    """
    Verify if a course fits the criteria provided.
    
    Args:
        course_info: Course information dictionary
        criteria: Criteria to check against
    
    Returns:
        Dictionary with fit assessment
    """
    # Simple verification logic
    course_name = course_info.get("name", "").lower()
    course_desc = course_info.get("description", "").lower()
    criteria_lower = criteria.lower()
    
    # Check if criteria keywords appear in course info
    keywords = criteria_lower.split()
    matches = sum(1 for keyword in keywords if keyword in course_name or keyword in course_desc)
    
    fit_score = (matches / len(keywords)) * 100 if keywords else 0
    
    return {
        "course": course_info.get("name"),
        "fit_score": fit_score,
        "meets_criteria": fit_score >= 50,
        "reasoning": f"Course matches {matches}/{len(keywords)} criteria keywords"
    }
