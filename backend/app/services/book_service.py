from app.core.database import supabase
from app.core.ai import generate_embeddings
from app.core.config import logger

# Import the query reformulation service
try:
    from app.services.query_reformulation import generate_search_queries, generate_synthesis_query
    QUERY_REFORMULATION_AVAILABLE = True
except ImportError:
    logger.warning("Query reformulation service not available for book service")
    QUERY_REFORMULATION_AVAILABLE = False

def get_context_from_book(query: str, top_k: int = 5, use_enhanced_queries: bool = True, project_info: str = "") -> tuple:
    """
    Retrieve context from the book chunks database
    
    Args:
        query: The search query
        top_k: Number of chunks to retrieve
        use_enhanced_queries: Whether to use query reformulation
        project_info: Additional project information to help contextualize the query
        
    Returns:
        tuple: A tuple containing (context_string, number_of_chunks_used)
    """
    try:
        all_chunks = []
        total_chunks_count = 0
        
        # Use query reformulation if available and enabled
        if QUERY_REFORMULATION_AVAILABLE and use_enhanced_queries:
            # Generate multiple search queries
            search_queries = generate_search_queries(query, num_queries=3, project_info=project_info)
            logger.info(f"Using enhanced queries for book: {search_queries}")
            
            # Get chunks for each search query
            for search_query in search_queries:
                query_embedding = generate_embeddings(search_query)
                chunks_data = supabase.rpc("match_book_chunks", {
                    "query_embedding": query_embedding,
                    "match_count": max(2, top_k // len(search_queries)),  # Distribute top_k among queries
                    "match_threshold": 0.4
                }).execute()
                
                if chunks_data.data:
                    # Add chunks to results, avoiding duplicates
                    for chunk in chunks_data.data:
                        # Use id as the identifier since chunk_id might not be available
                        chunk_id = chunk.get("id")
                        if not any(existing.get("id") == chunk_id for existing in all_chunks):
                            all_chunks.append(chunk)
                            total_chunks_count += 1
                            
            # If we didn't get enough chunks, try a synthesis query as well
            if total_chunks_count < top_k and QUERY_REFORMULATION_AVAILABLE:
                synthesis_query = generate_synthesis_query(query, project_info=project_info)
                logger.info(f"Using synthesis query for book: {synthesis_query}")
                
                query_embedding = generate_embeddings(synthesis_query)
                chunks_data = supabase.rpc("match_book_chunks", {
                    "query_embedding": query_embedding,
                    "match_count": top_k - total_chunks_count,
                    "match_threshold": 0.4
                }).execute()
                
                if chunks_data.data:
                    # Add chunks to results, avoiding duplicates
                    for chunk in chunks_data.data:
                        chunk_id = chunk.get("id")
                        if not any(existing.get("id") == chunk_id for existing in all_chunks):
                            all_chunks.append(chunk)
                            total_chunks_count += 1
        else:
            # Standard single query approach
            query_embedding = generate_embeddings(query)
            chunks_data = supabase.rpc("match_book_chunks", {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "match_threshold": 0.4
            }).execute()
            
            logger.info(f"Book chunks response data: {chunks_data}")
            
            if chunks_data.data:
                all_chunks = chunks_data.data
                total_chunks_count = len(all_chunks)
        
        if not all_chunks:
            logger.warning("No matching chunks found in the book")
            return "", 0
            
        # Extract and join the text from the chunks
        relevant_chunks = []
        for item in all_chunks:
            # The SQL function aliases raw_text as content
            chunk_text = item.get("content") 
            if chunk_text:
                # Log each chunk's first 100 characters for debugging
                logger.info(f"Retrieved chunk (first 100 chars): {chunk_text[:100]}...")
                relevant_chunks.append(chunk_text)
                
        if not relevant_chunks:
            logger.warning("No content found in the retrieved chunks")
            return "", 0
                
        context = "\n\n".join(relevant_chunks)
        
        logger.info(f"Retrieved {len(relevant_chunks)} chunks from book for query: {query}")
        return context, len(relevant_chunks)
    except Exception as e:
        logger.error(f"Error retrieving context from book: {e}")
        return "", 0 