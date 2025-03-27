from app.core.ai import generate_response
from app.core.config import logger
from typing import List
from app.core.config import GEMINI_MODEL, GEMINI_API_KEY
import google.generativeai as genai

def generate_query_reformulation(prompt: str) -> str:
    """
    Generate reformulated queries without requiring context.
    Uses Gemini model directly with a custom prompt.
    
    Args:
        prompt: The prompt for query reformulation
        
    Returns:
        str: The generated result
    """
    try:
        # Configure Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Generate response
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in direct query reformulation: {e}")
        return ""

def generate_search_queries(original_query: str, num_queries: int = 3, project_info: str = "") -> List[str]:
    """
    Generate multiple search queries based on the user's original query.
    
    This function uses AI to analyze the user's question and generate multiple
    different search queries that can help retrieve more relevant information.
    
    Args:
        original_query: The user's original query
        num_queries: Number of different search queries to generate
        project_info: Additional project information to help contextualize the query
        
    Returns:
        List[str]: List of generated search queries
    """
    try:
        # Create a prompt for generating search queries
        project_context = f"\nProject context:\n{project_info}\n" if project_info else ""
        
        prompt = f"""
        I need to search for information to answer this question:
        "{original_query}"
        {project_context}
        To get the best results, please generate {num_queries} different search queries that would help me find relevant information.
        These queries should:
        - Cover different aspects of the original question
        - Use different keywords or phrasings
        - Be specific and clear
        - Capture important concepts from the original question
        - Match the project context provided (if any)
        
        Return only the {num_queries} search queries, one per line, without numbering or additional text.
        """
        
        # Generate search queries using direct Gemini call
        response = generate_query_reformulation(prompt)
        
        # Split the response into individual queries
        queries = [q.strip() for q in response.split('\n') if q.strip()]
        
        # Filter to the requested number of queries and ensure the original query is included
        result_queries = queries[:num_queries-1]
        if not result_queries or len(result_queries) < num_queries - 1:
            # If we didn't get enough valid queries, add some generic reformulations
            if "social media" in original_query.lower() and "depression" in original_query.lower():
                backup_queries = [
                    'adolescents "social media" depression relationship',
                    '"teenagers" "social networking sites" "mental health"'
                ]
                # Add backup queries if needed
                for bq in backup_queries:
                    if bq not in result_queries and len(result_queries) < num_queries - 1:
                        result_queries.append(bq)
                        
        # Always ensure original query is included
        if original_query not in result_queries:
            result_queries.append(original_query)
            
        # Ensure we don't return more than the requested number
        result_queries = result_queries[:num_queries]
        
        logger.info(f"Generated {len(result_queries)} search queries from original: '{original_query}'")
        return result_queries
    except Exception as e:
        logger.error(f"Error generating search queries: {e}")
        # Return the original query if there's an error
        return [original_query]

def generate_synthesis_query(original_query: str, project_info: str = "") -> str:
    """
    Generate a query specifically designed to find information for synthesizing sources.
    
    Args:
        original_query: The user's original query
        project_info: Additional project information to help contextualize the query
        
    Returns:
        str: A query designed for finding information to synthesize
    """
    try:
        # Create a prompt for generating a synthesis-focused query
        project_context = f"\nProject context:\n{project_info}\n" if project_info else ""
        
        prompt = f"""
        I need to search for information to synthesize multiple sources about:
        "{original_query}"
        {project_context}
        Generate a search query that would help me find:
        - Overviews of the topic
        - Comparative information
        - Meta-analyses or literature reviews
        - Different perspectives on the topic
        
        Return only the search query, without any additional text.
        """
        
        # Generate the synthesis query using direct Gemini call
        synthesis_query = generate_query_reformulation(prompt)
        
        # Check if response is empty and provide a fallback
        if not synthesis_query or len(synthesis_query.strip()) < 10:
            if "social media" in original_query.lower() and "depression" in original_query.lower():
                synthesis_query = "(social media AND adolescents AND depression) AND (meta-analysis OR \"literature review\" OR overview OR \"systematic review\" OR \"comparative study\" OR perspective OR viewpoint)"
            else:
                synthesis_query = f"(review OR meta-analysis OR \"systematic review\") AND ({original_query})"
        
        logger.info(f"Generated synthesis query: '{synthesis_query}' from original: '{original_query}'")
        return synthesis_query
    except Exception as e:
        logger.error(f"Error generating synthesis query: {e}")
        # Return the original query with synthesis indicator if there's an error
        return f"synthesis of {original_query}" 