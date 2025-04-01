from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from typing import List, Dict
from app.core.config import (
    EMBEDDING_MODEL, 
    USE_TRUST_REMOTE_CODE, 
    GEMINI_API_KEY, 
    GEMINI_MODEL,
    logger
)

# Initialize embedding model
try:
    embedder = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=USE_TRUST_REMOTE_CODE)
    logger.info(f"Embedding model {EMBEDDING_MODEL} initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize embedding model: {e}")
    # Create a mock embedder for development/testing
    from unittest.mock import MagicMock
    embedder = MagicMock()
    embedder.encode.return_value = [0.0] * 768  # Return a vector of zeros
    logger.warning("Using mock embedding model. Vector search features will not work correctly.")

# Initialize Gemini model
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(GEMINI_MODEL)
    logger.info(f"Gemini model {GEMINI_MODEL} initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini model: {e}")
    # Create a mock Gemini model for development/testing
    from unittest.mock import MagicMock
    gemini_model = MagicMock()
    gemini_model.generate_content.return_value.text = "This is a mock response. The Gemini API is not available."
    logger.warning("Using mock Gemini model. AI responses will not be accurate.")

def generate_embeddings(text: str) -> List[float]:
    """Generate embeddings for a given text"""
    try:
        if not text or not isinstance(text, str):
            logger.warning(f"Invalid text for embedding: {type(text)}")
            return [0.0] * 768
            
        # Get raw embeddings
        raw_embeddings = embedder.encode(text)
        
        # Convert to list if not already
        if hasattr(raw_embeddings, 'tolist'):
            embeddings = raw_embeddings.tolist()
        else:
            embeddings = list(raw_embeddings)
        
        # Ensure all values are proper floats
        if embeddings and isinstance(embeddings, list):
            try:
                # Convert all elements to float and handle potential nesting
                clean_embeddings = []
                for item in embeddings:
                    if isinstance(item, (int, float)):
                        clean_embeddings.append(float(item))
                    elif isinstance(item, str):
                        try:
                            clean_embeddings.append(float(item))
                        except ValueError:
                            # Skip items that can't be converted
                            logger.warning(f"Skipping non-numeric embedding value: {item}")
                    else:
                        # Try to get a numeric value, otherwise use 0.0
                        try:
                            clean_embeddings.append(float(item))
                        except (ValueError, TypeError):
                            clean_embeddings.append(0.0)
                
                # If we ended up with an empty list, use zeros
                if not clean_embeddings:
                    logger.warning("Failed to get valid embeddings, using zeros")
                    return [0.0] * 768
                    
                return clean_embeddings
            except Exception as e:
                logger.error(f"Failed to clean embedding values: {e}", exc_info=True)
                return [0.0] * 768
        
        # Return what we have, or zeros if nothing valid
        return embeddings if embeddings else [0.0] * 768
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}", exc_info=True)
        # Return a vector of zeros as fallback
        return [0.0] * 768

def generate_response(query: str, context: str, chat_history: List[Dict[str, str]] = None, project_info: str = "") -> str:
    """
    Generate a response using Gemini model
    
    Args:
        query: The user's query
        context: The context information retrieved from sources
        chat_history: Optional chat history for conversational context
        project_info: Additional information about the project
        
    Returns:
        str: The generated response
    """
    try:
        # Format chat history if provided
        history_text = ""
        if chat_history and len(chat_history) > 0:
            history_text = "Previous conversation:\n"
            for msg in chat_history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_text += f"{role}: {msg.get('content')}\n"
            history_text += "\n"
        
        # Check if context is empty or very short
        if not context or len(context.strip()) < 20:
            logger.warning(f"Empty or very short context provided for query: {query}")
            return "I don't have enough information in my knowledge base to answer this question accurately. Please try a different question or consider uploading relevant documents to your project."
        
        # Log the first 200 characters of context for debugging
        logger.info(f"Context first 200 chars: {context[:200]}...")
        
        # Include project info in prompt if available
        project_section = ""
        if project_info:
            project_section = f"""
            ### Project Information:
            {project_info}
            
            Use this project information to tailor your response to the user's specific research context.
            """
            logger.info(f"Including project info in prompt: {project_info[:100]}...")
        
        # Check for research questions related to certain topics
        research_topics = ["social media", "depression", "anxiety", "mental health", "adolescents", "teenagers"]
        is_research_question = any(topic in query.lower() for topic in research_topics) or (
            project_info and any(topic in project_info.lower() for topic in research_topics)
        )
        
        if is_research_question:
            prompt = f"""
            ### Task:
            You are a research assistant analyzing a query about {query}.
            
            {project_section}
            
            The context provided may contain two types of information:
            1. Content from specific research sources about the topic (social media, depression, etc.)
            2. Research methodology guidance from a research design book
            
            If the context contains SPECIFIC RESEARCH FINDINGS about {query}, provide a detailed response using that information.
            
            If the context ONLY contains research methodology guidance (not specific content on {query}), your response should:
            1. Acknowledge that you don't have specific findings on {query}
            2. Provide research methodology guidance on how the user could approach studying this topic
            3. Explain how they could structure their own research on {query}
            4. Suggest what kinds of sources or papers they might want to upload to get more specific information
            
            If you have project information available, make sure your response is tailored to:
            - The research type indicated in the project
            - The learning objectives of the project
            - The specific context of the current question
            
            Example response format when only methodology content is available:
            "Based on the available research sources, I don't have specific findings about the relationship between social media use and depression in adolescents. However, I can offer methodological guidance on how to approach this research topic:
            
            [Provide methodology guidance from the context that would be helpful for researching this specific topic]
            
            To get specific research findings on this topic, consider uploading meta-analyses, systematic reviews, or empirical studies that directly examine the relationship between social media use and adolescent depression."
            
            {history_text}
            
            ### Query:
            {query}
            
            ### Context:
            {context}
            """
        else:
            prompt = f"""
            ### Task:
            Answer the user's query using ONLY the provided context. The context contains relevant information from research sources.
            
            {project_section}
            
            If the provided context contains information relevant to the query, provide a concise, helpful response based on that information.
            
            If you have project information available, make sure your response is tailored to:
            - The research type indicated in the project
            - The learning objectives of the project
            - The specific context of the current question
            
            If the context does NOT contain sufficient information to answer the query, respond with: 
            "Based on the available research sources, I don't have enough specific information to answer your question about {query}. You might want to upload more relevant documents to your project."
            
            {history_text}
            
            ### Query:
            {query}
            
            ### Context:
            {context}
            """
        
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f"I encountered an error generating a response. Please try again or check your API configuration: {str(e)}"

def calculate_similarity(vector1: List[float], vector2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vector1: First vector
        vector2: Second vector
        
    Returns:
        Cosine similarity value between 0 and 1
    """
    try:
        import numpy as np
        import ast
        import re
        
        if not vector1 or not vector2:
            return 0.0
        
        # Function to safely parse a value to float
        def safe_parse_float(value):
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # If it looks like a list representation, try to parse it
                if value.startswith('[') or value.startswith('('):
                    try:
                        # Try to parse as a literal
                        parsed = ast.literal_eval(value)
                        # If it's a list or tuple, return the first element if possible
                        if isinstance(parsed, (list, tuple)) and parsed:
                            return safe_parse_float(parsed[0])
                        return 0.0
                    except (ValueError, SyntaxError):
                        return 0.0
                # Try to convert the string directly to float
                try:
                    return float(value)
                except ValueError:
                    return 0.0
            return 0.0
        
        # Ensure vectors contain only numeric values
        try:
            # Try to convert each element to float with safe parsing
            vec1 = np.array([safe_parse_float(x) for x in vector1])
            vec2 = np.array([safe_parse_float(x) for x in vector2])
            
            # Check if vectors are valid
            if len(vec1) == 0 or len(vec2) == 0:
                return 0.0
                
            # Check if vectors contain any non-zero values
            if np.all(vec1 == 0) or np.all(vec2 == 0):
                return 0.0
                
            # Check dimensions - if they don't match, return a default score 
            # instead of attempting to calculate similarity
            if len(vec1) != len(vec2):
                logger.warning(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}. Skipping similarity calculation.")
                # Return a low similarity score for mismatched dimensions
                return 0.1
                
        except Exception as e:
            logger.error(f"Error converting vectors to numeric format: {e}", exc_info=True)
            return 0.0
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    except Exception as e:
        logger.error(f"Error calculating similarity: {str(e)}", exc_info=True)
        return 0.0

async def gemini_generate_content(prompt: str) -> str:
    """
    Generate content using Gemini model asynchronously
    
    Args:
        prompt: The prompt to send to Gemini
        
    Returns:
        str: The generated text response
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error in async content generation: {e}")
        return f"Error generating content: {str(e)}" 