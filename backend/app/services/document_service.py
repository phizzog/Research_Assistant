from app.core.database import supabase
from app.core.ai import generate_embeddings
from app.models.schemas import ParserOutput
from app.core.config import logger
from typing import List, Dict, Any, Tuple
import time
import os

# Import the query reformulation service
try:
    from app.services.query_reformulation import generate_search_queries, generate_synthesis_query
    QUERY_REFORMULATION_AVAILABLE = True
except ImportError:
    logger.warning("Query reformulation service not available")
    QUERY_REFORMULATION_AVAILABLE = False

async def store_pdf_content(pdf_data: ParserOutput, project_id: int = None) -> int:
    """
    Store the parsed PDF content in Supabase for later retrieval.
    This function creates chunks of text and stores them with embeddings.
    
    Args:
        pdf_data: Parsed PDF data
        project_id: Optional project ID to associate with the chunks
    
    Returns:
        int: Number of chunks stored
    """
    try:
        logger.info(f"Storing PDF content with project_id={project_id}")
        
        # Extract all text from the PDF
        all_text = []
        for page in pdf_data.pages:
            # Add page text
            if page.text:
                all_text.append(f"Page {page.page_id}: {page.text}")
            
            # Add table text if available
            for table in page.tables:
                table_text = "\n".join([" | ".join(row) for row in table.data])
                if table_text:
                    all_text.append(f"Table {table.table_id}: {table_text}")
        
        # Join all text
        full_text = "\n\n".join(all_text)
        
        # Create chunks (simple approach - split by paragraphs)
        chunks = [chunk for chunk in full_text.split("\n\n") if chunk.strip()]
        
        # Create a source_id from the document filename with timestamp to ensure uniqueness
        document_id = pdf_data.document.document_id
        timestamp = int(time.time())
        source_id = f"source_{document_id}_{timestamp}"
        
        # Store each chunk with its embedding
        chunks_stored = 0
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = generate_embeddings(chunk)
            
            # Create a unique chunk_id
            chunk_id = f"{document_id}_{timestamp}_{i}"
            
            # Create payload including project_id if provided
            payload = {
                "source_id": source_id,
                "chunk_id": chunk_id,
                "raw_text": chunk,
                "embedding": embedding,
                "metadata": {
                    "source": pdf_data.document.filename,
                    "chunk_index": i,
                    "document_id": document_id
                }
            }
            
            # Add project_id if provided - set it both at the root level and in metadata
            if project_id is not None:
                try:
                    # Convert to integer if it's not already
                    project_id_int = int(project_id)
                    payload["project_id"] = project_id_int
                    payload["metadata"]["project_id"] = project_id_int
                    logger.info(f"Adding project_id={project_id_int} to chunk {i+1}/{len(chunks)}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting project_id to int: {e}")
                    logger.info(f"Using original project_id={project_id} without conversion")
                    payload["project_id"] = project_id
                    payload["metadata"]["project_id"] = project_id
            
            # Log the complete payload for the first chunk for debugging
            if i == 0:
                logger.info(f"Sample payload for first chunk (truncated text): {payload['raw_text'][:100]}...")
                logger.info(f"Payload project_id: {payload.get('project_id')}")
                logger.info(f"Payload keys: {list(payload.keys())}")
            
            # Define the columns to include explicitly (CRITICAL FIX)
            columns = ["chunk_id", "source_id", "raw_text", "embedding", "metadata"]
            
            # Add project_id to columns list if it's in the payload
            if "project_id" in payload:
                columns.append("project_id")
                logger.info(f"Explicitly including project_id in columns: {columns}")
            
            # Store in Supabase using the sources table with explicit columns
            logger.info(f"Executing Supabase upsert for chunk {i+1} with columns: {columns}")
            
            # Use proper explicit upsert with columns list
            response = supabase.table("sources").upsert(
                payload,
                on_conflict="chunk_id",
                returning="minimal"
            ).execute()
                
            if response.data:
                chunks_stored += 1
                if i % 10 == 0 or i == len(chunks) - 1:  # Log every 10 chunks and the last one
                    logger.info(f"Stored chunk {i+1}/{len(chunks)} with project_id={project_id}")
        
        logger.info(f"Stored {chunks_stored}/{len(chunks)} chunks from PDF {pdf_data.document.filename} with project_id={project_id}")
        return chunks_stored
    except Exception as e:
        logger.error(f"Error storing PDF content: {e}")
        raise

def get_context_from_query(query: str, top_k: int = 5, use_enhanced_queries: bool = True) -> str:
    """
    Retrieve context from Supabase based on query
    
    Args:
        query: The search query
        top_k: Number of chunks to retrieve
        use_enhanced_queries: Whether to use query reformulation
        
    Returns:
        str: Concatenated context
    """
    try:
        all_chunks = []
        total_chunks_count = 0
        
        # Use query reformulation if available and enabled
        if QUERY_REFORMULATION_AVAILABLE and use_enhanced_queries:
            # Generate multiple search queries
            search_queries = generate_search_queries(query, num_queries=3)
            logger.info(f"Using enhanced queries: {search_queries}")
            
            # Get chunks for each search query
            for search_query in search_queries:
                query_embedding = generate_embeddings(search_query)
                chunks_data = supabase.rpc("match_sources", {
                    "query_embedding": query_embedding,
                    "match_count": max(2, top_k // len(search_queries))  # Distribute top_k among queries
                }).execute()
                
                if chunks_data.data:
                    # Add chunks to results, avoiding duplicates
                    for chunk in chunks_data.data:
                        chunk_id = chunk.get("chunk_id")
                        if not any(existing.get("chunk_id") == chunk_id for existing in all_chunks):
                            all_chunks.append(chunk)
                            total_chunks_count += 1
        else:
            # Standard single query approach
            query_embedding = generate_embeddings(query)
            chunks_data = supabase.rpc("match_sources", {
                "query_embedding": query_embedding,
                "match_count": top_k
            }).execute()
            
            if chunks_data.data:
                all_chunks = chunks_data.data
                total_chunks_count = len(all_chunks)
                
        if not all_chunks:
            logger.warning("No matching chunks found")
            return ""
        
        # Extract and join the text from the chunks
        relevant_chunks = [item.get("raw_text", "") for item in all_chunks if item.get("raw_text")]
        context = "\n\n".join(relevant_chunks)
        
        logger.info(f"Retrieved {total_chunks_count} chunks for query: {query}")
        return context
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return ""

def get_context_for_project(
    query: str, 
    project_id: int, 
    top_k: int = 5, 
    use_enhanced_queries: bool = True,
    project_info: str = ""
) -> str:
    """
    Retrieve context from Supabase based on query, filtered by project_id
    
    Args:
        query: The search query
        project_id: The project ID to filter sources by
        top_k: Number of chunks to retrieve
        use_enhanced_queries: Whether to use query reformulation
        project_info: Additional project information for query reformulation
        
    Returns:
        str: Concatenated context
    """
    try:
        all_chunks = []
        total_chunks_count = 0
        
        # Use query reformulation if available and enabled
        if QUERY_REFORMULATION_AVAILABLE and use_enhanced_queries:
            # Generate multiple search queries
            search_queries = generate_search_queries(query, num_queries=3, project_info=project_info)
            logger.info(f"Using enhanced queries for project {project_id}: {search_queries}")
            
            # Get chunks for each search query
            for search_query in search_queries:
                query_embedding = generate_embeddings(search_query)
                chunks_data = supabase.rpc("match_sources_by_project", {
                    "query_embedding": query_embedding,
                    "p_project_id": project_id,
                    "match_count": max(2, top_k // len(search_queries))  # Distribute top_k among queries
                }).execute()
                
                if chunks_data.data:
                    # Add chunks to results, avoiding duplicates
                    for chunk in chunks_data.data:
                        chunk_id = chunk.get("chunk_id")
                        if not any(existing.get("chunk_id") == chunk_id for existing in all_chunks):
                            all_chunks.append(chunk)
                            total_chunks_count += 1
                            
            # If we didn't get enough chunks, try a synthesis query as well
            if total_chunks_count < top_k and QUERY_REFORMULATION_AVAILABLE:
                synthesis_query = generate_synthesis_query(query, project_info=project_info)
                logger.info(f"Using synthesis query for project {project_id}: {synthesis_query}")
                
                query_embedding = generate_embeddings(synthesis_query)
                chunks_data = supabase.rpc("match_sources_by_project", {
                    "query_embedding": query_embedding,
                    "p_project_id": project_id,
                    "match_count": top_k - total_chunks_count
                }).execute()
                
                if chunks_data.data:
                    # Add chunks to results, avoiding duplicates
                    for chunk in chunks_data.data:
                        chunk_id = chunk.get("chunk_id")
                        if not any(existing.get("chunk_id") == chunk_id for existing in all_chunks):
                            all_chunks.append(chunk)
                            total_chunks_count += 1
        else:
            # Standard single query approach
            query_embedding = generate_embeddings(query)
            chunks_data = supabase.rpc("match_sources_by_project", {
                "query_embedding": query_embedding,
                "p_project_id": project_id,
                "match_count": top_k
            }).execute()
            
            if chunks_data.data:
                all_chunks = chunks_data.data
                total_chunks_count = len(all_chunks)
                
        if not all_chunks:
            logger.warning(f"No matching chunks found for project_id: {project_id}")
            return ""
            
        # Extract and join the text from the chunks
        relevant_chunks = [item.get("raw_text", "") for item in all_chunks if item.get("raw_text")]
        context = "\n\n".join(relevant_chunks)
        
        logger.info(f"Retrieved {total_chunks_count} chunks for query: {query} in project: {project_id}")
        return context
    except Exception as e:
        logger.error(f"Error retrieving context for project: {e}")
        return ""

def get_context_for_project_with_selected_documents(
    query: str, 
    project_id: int, 
    selected_document_ids: List[str],
    top_k: int = 5,
    use_enhanced_queries: bool = True,
    project_info: str = ""
) -> str:
    """
    Retrieve context from Supabase based on query, filtered by project_id and document_ids
    
    Args:
        query: The search query
        project_id: The project ID to filter sources by
        selected_document_ids: List of document IDs to include in the search
        top_k: Number of chunks to retrieve
        use_enhanced_queries: Whether to use query reformulation
        project_info: Additional project information for query reformulation
        
    Returns:
        str: Concatenated context
    """
    try:
        # When no document IDs are selected, fall back to the standard project query
        if not selected_document_ids:
            return get_context_for_project(query, project_id, top_k, use_enhanced_queries, project_info)
        
        logger.info(f"Searching for selected document IDs: {selected_document_ids} in project {project_id}")
        
        all_chunks = []
        total_chunks_count = 0
        
        # Use query reformulation if available and enabled
        if QUERY_REFORMULATION_AVAILABLE and use_enhanced_queries:
            # Generate multiple search queries
            search_queries = generate_search_queries(query, num_queries=3, project_info=project_info)
            logger.info(f"Using enhanced queries for project {project_id} with selected docs: {search_queries}")
            
            # Get chunks for each search query
            for search_query in search_queries:
                query_embedding = generate_embeddings(search_query)
                chunks_data = supabase.rpc("match_sources_by_project", {
                    "query_embedding": query_embedding,
                    "p_project_id": project_id,
                    "match_count": top_k * 3  # Get more results than needed to allow for filtering
                }).execute()
                
                logger.info(f"Retrieved {len(chunks_data.data) if chunks_data.data else 0} chunks from project {project_id} for query: {search_query}")
                
                if chunks_data.data:
                    # Filter chunks by document_id from metadata and add to results, avoiding duplicates
                    document_matches_found = set()
                    for chunk in chunks_data.data:
                        # Extract document_id from metadata
                        metadata = chunk.get("metadata", {})
                        document_id = metadata.get("document_id", "")
                        source = metadata.get("source", "")
                        
                        # Log detailed info for debugging
                        if document_id:
                            logger.info(f"Found chunk with document_id: {document_id}, source: {source}")
                        else:
                            logger.info(f"Chunk missing document_id in metadata: {metadata}")
                        
                        # Try different matching approaches
                        is_match = False
                        
                        # Direct match with document_id
                        if document_id and document_id in selected_document_ids:
                            is_match = True
                            logger.info(f"Direct match with document_id: {document_id}")
                        
                        # Match with source (filename)
                        elif source and source in selected_document_ids:
                            is_match = True
                            logger.info(f"Direct match with source: {source}")
                        
                        # Try partial matches (for temporary file names)
                        else:
                            for selected_id in selected_document_ids:
                                # Check if the temporary filename prefix (e.g., 'tmp') is in either field
                                if (document_id and selected_id in document_id) or (source and selected_id in source):
                                    is_match = True
                                    logger.info(f"Partial match: selected_id={selected_id}, document_id={document_id}, source={source}")
                                    break
                                # Also check the reverse (document_id is in selected_id)
                                elif document_id and document_id in selected_id:
                                    is_match = True
                                    logger.info(f"Reverse partial match: document_id={document_id} in selected_id={selected_id}")
                                    break
                                # Try matching just the filename without path (more lenient matching)
                                elif document_id and os.path.basename(document_id) == os.path.basename(selected_id):
                                    is_match = True
                                    logger.info(f"Basename match: document_id basename={os.path.basename(document_id)}, selected_id basename={os.path.basename(selected_id)}")
                                    break
                        
                        # Include the chunk if it's a match
                        if is_match:
                            document_matches_found.add(document_id or source)
                            chunk_id = chunk.get("chunk_id")
                            if not any(existing.get("chunk_id") == chunk_id for existing in all_chunks):
                                all_chunks.append(chunk)
                                total_chunks_count += 1
                                
                        # Break early if we have enough chunks
                        if total_chunks_count >= top_k:
                            break
                    
                    # Log matches found for debugging
                    logger.info(f"Document matches found: {document_matches_found} out of selected: {selected_document_ids}")
            
            # If we didn't get enough chunks, try a synthesis query as well
            if total_chunks_count < top_k and QUERY_REFORMULATION_AVAILABLE:
                synthesis_query = generate_synthesis_query(query, project_info=project_info)
                logger.info(f"Using synthesis query for project {project_id} with selected docs: {synthesis_query}")
                
                query_embedding = generate_embeddings(synthesis_query)
                chunks_data = supabase.rpc("match_sources_by_project", {
                    "query_embedding": query_embedding,
                    "p_project_id": project_id,
                    "match_count": top_k * 3  # Get more results than needed to allow for filtering
                }).execute()
                
                if chunks_data.data:
                    # Apply same matching logic as above
                    for chunk in chunks_data.data:
                        metadata = chunk.get("metadata", {})
                        document_id = metadata.get("document_id", "")
                        source = metadata.get("source", "")
                        
                        # Try different matching approaches
                        is_match = False
                        
                        # Direct match
                        if document_id and document_id in selected_document_ids:
                            is_match = True
                        elif source and source in selected_document_ids:
                            is_match = True
                        
                        # Partial matches for temporary files
                        else:
                            for selected_id in selected_document_ids:
                                if (document_id and selected_id in document_id) or (source and selected_id in source):
                                    is_match = True
                                    break
                                elif document_id and document_id in selected_id:
                                    is_match = True
                                    break
                        
                        if is_match:
                            chunk_id = chunk.get("chunk_id")
                            if not any(existing.get("chunk_id") == chunk_id for existing in all_chunks):
                                all_chunks.append(chunk)
                                total_chunks_count += 1
                                
                        # Break early if we have enough chunks
                        if total_chunks_count >= top_k:
                            break
        else:
            # Standard single query approach with same matching logic
            query_embedding = generate_embeddings(query)
            chunks_data = supabase.rpc("match_sources_by_project", {
                "query_embedding": query_embedding,
                "p_project_id": project_id,
                "match_count": top_k * 3  # Get more results than needed to allow for filtering
            }).execute()
            
            if chunks_data.data:
                # Filter chunks by document_id from metadata
                filtered_chunks = []
                for chunk in chunks_data.data:
                    # Extract document_id from metadata
                    metadata = chunk.get("metadata", {})
                    document_id = metadata.get("document_id", "")
                    source = metadata.get("source", "")
                    
                    # Try different matching approaches
                    is_match = False
                    
                    # Direct match
                    if document_id and document_id in selected_document_ids:
                        is_match = True
                    elif source and source in selected_document_ids:
                        is_match = True
                    
                    # Partial matches for temporary files
                    else:
                        for selected_id in selected_document_ids:
                            if (document_id and selected_id in document_id) or (source and selected_id in source):
                                is_match = True
                                break
                            elif document_id and document_id in selected_id:
                                is_match = True
                                break
                    
                    if is_match:
                        filtered_chunks.append(chunk)
                        
                    # Break early if we have enough chunks
                    if len(filtered_chunks) >= top_k:
                        break
                        
                all_chunks = filtered_chunks
                total_chunks_count = len(all_chunks)
        
        # If no chunks match the selected documents, return empty string
        if not all_chunks:
            logger.warning(f"No chunks match the selected document IDs: {selected_document_ids}")
            return ""
            
        # Extract and join the text from the filtered chunks
        relevant_chunks = []
        for item in all_chunks:
            chunk_text = item.get("raw_text", "")
            metadata = item.get("metadata", {})
            document_id = metadata.get("document_id", "unknown")
            
            if chunk_text:
                # Log each chunk's first 100 characters for debugging
                logger.info(f"Retrieved project chunk from document {document_id} (first 100 chars): {chunk_text[:100]}...")
                relevant_chunks.append(chunk_text)
        
        context = "\n\n".join(relevant_chunks)
        
        logger.info(f"Retrieved {len(relevant_chunks)} chunks for query: {query} in project: {project_id} with selected document IDs: {selected_document_ids}")
        return context
    except Exception as e:
        logger.error(f"Error retrieving context for project with selected documents: {e}")
        return ""

# Implement the missing helper functions for document service

def fetch_document_chunks(supabase, project_id: str, query: str) -> List[dict]:
    """
    Fetch document chunks for a project based on query.
    
    Args:
        supabase: Supabase client instance
        project_id: ID of the project
        query: Search query
        
    Returns:
        List[dict]: List of document chunks
    """
    try:
        # Generate embedding for the query
        query_embedding = generate_embeddings(query)
        
        # Search for chunks with semantic similarity
        response = supabase.rpc("match_sources_by_project", {
            "query_embedding": query_embedding,
            "p_project_id": project_id,
            "match_count": 20  # Get more results than needed for better ranking
        }).execute()
        
        logger.info(f"Fetched {len(response.data) if response.data else 0} chunks for project {project_id} with query: {query}")
        return response.data or []
    except Exception as e:
        logger.error(f"Error in fetch_document_chunks: {str(e)}", exc_info=True)
        return []

def fetch_document_chunks_from_selected_documents(supabase, project_id: str, document_ids: List[str], query: str) -> List[dict]:
    """
    Fetch document chunks from selected documents based on query.
    
    Args:
        supabase: Supabase client instance
        project_id: ID of the project
        document_ids: List of document IDs to search within
        query: Search query
        
    Returns:
        List[dict]: List of document chunks
    """
    try:
        # Generate embedding for the query
        query_embedding = generate_embeddings(query)
        
        # Search for chunks with semantic similarity
        response = supabase.rpc("match_sources_by_project", {
            "query_embedding": query_embedding,
            "p_project_id": project_id,
            "match_count": 50  # Get more results than needed for filtering
        }).execute()
        
        if not response.data:
            return []
            
        # Filter chunks by document_id
        filtered_chunks = []
        for chunk in response.data:
            metadata = chunk.get("metadata", {})
            document_id = metadata.get("document_id", "")
            source = metadata.get("source", "")
            
            # Try different matching approaches
            is_match = False
            
            # Direct match
            if document_id and document_id in document_ids:
                is_match = True
                logger.info(f"Direct match with document_id: {document_id}")
            elif source and source in document_ids:
                is_match = True
                logger.info(f"Direct match with source: {source}")
            
            # Try partial matches for temporary files
            else:
                for selected_id in document_ids:
                    # Check for partial matches in both directions
                    if ((document_id and selected_id in document_id) or 
                        (source and selected_id in source) or
                        (document_id and document_id in selected_id)):
                        is_match = True
                        logger.info(f"Partial match: selected_id={selected_id}, document_id={document_id}")
                        break
                    # Check basename matching
                    elif document_id and os.path.basename(document_id) == os.path.basename(selected_id):
                        is_match = True
                        logger.info(f"Basename match: document_id={document_id}, selected_id={selected_id}")
                        break
            
            if is_match:
                filtered_chunks.append(chunk)
        
        logger.info(f"Fetched {len(filtered_chunks)} chunks from selected documents in project {project_id}")
        return filtered_chunks
    except Exception as e:
        logger.error(f"Error in fetch_document_chunks_from_selected_documents: {str(e)}", exc_info=True)
        return []

def fetch_all_document_chunks(supabase, project_id: str) -> List[dict]:
    """
    Fetch all document chunks for a project without performing a search.
    
    Args:
        supabase: Supabase client instance
        project_id: ID of the project
        
    Returns:
        List[dict]: List of document chunks
    """
    try:
        # Retrieve all chunks for the project
        response = supabase.table("sources").select("*").eq("project_id", project_id).execute()
        
        logger.info(f"Fetched {len(response.data) if response.data else 0} chunks from project {project_id}")
        return response.data or []
    except Exception as e:
        logger.error(f"Error in fetch_all_document_chunks: {str(e)}", exc_info=True)
        return []

def rank_chunks_by_relevance(chunks: List[dict], query: str) -> List[dict]:
    """
    Rank chunks by relevance to the query.
    
    Args:
        chunks: List of document chunks
        query: User query to rank against
        
    Returns:
        List[dict]: List of chunks sorted by relevance
    """
    try:
        if not chunks:
            return []
            
        # Generate embedding for the query
        query_embedding = generate_embeddings(query)
        
        # For each chunk, calculate similarity with the query
        for chunk in chunks:
            # If the chunk already has a similarity score, keep it
            if "similarity" in chunk:
                continue
                
            # If the chunk has an embedding, calculate similarity
            if "embedding" in chunk and chunk["embedding"]:
                from app.core.ai import calculate_similarity
                similarity = calculate_similarity(query_embedding, chunk["embedding"])
                chunk["similarity"] = similarity
            else:
                # If no embedding, use a default low similarity
                chunk["similarity"] = 0.1
        
        # Sort chunks by similarity (highest first)
        sorted_chunks = sorted(chunks, key=lambda x: x.get("similarity", 0), reverse=True)
        
        logger.info(f"Ranked {len(sorted_chunks)} chunks by relevance to query: {query}")
        return sorted_chunks
    except Exception as e:
        logger.error(f"Error in rank_chunks_by_relevance: {str(e)}", exc_info=True)
        # Return the original chunks if ranking fails
        return chunks

def select_top_chunks(chunks: List[dict], max_tokens: int = 6000) -> Tuple[List[dict], int]:
    """
    Select top chunks based on relevance, up to a maximum token limit.
    
    Args:
        chunks: List of chunks sorted by relevance
        max_tokens: Maximum number of tokens to include
        
    Returns:
        Tuple[List[dict], int]: List of selected chunks and the number used
    """
    try:
        if not chunks:
            return [], 0
            
        selected_chunks = []
        total_tokens = 0
        num_chunks_used = 0
        
        for chunk in chunks:
            chunk_text = chunk.get("raw_text", "")
            # Estimate token count (rough approximation: 4 chars per token)
            token_estimate = len(chunk_text) // 4
            
            # If adding this chunk would exceed the token limit, stop
            if total_tokens + token_estimate > max_tokens and selected_chunks:
                break
                
            selected_chunks.append(chunk)
            total_tokens += token_estimate
            num_chunks_used += 1
        
        logger.info(f"Selected {num_chunks_used} chunks with approximately {total_tokens} tokens")
        return selected_chunks, num_chunks_used
    except Exception as e:
        logger.error(f"Error in select_top_chunks: {str(e)}", exc_info=True)
        # Return a subset of chunks if selection fails
        safe_max = min(3, len(chunks))
        return chunks[:safe_max], safe_max

def format_context_from_chunks(chunks: List[dict]) -> str:
    """
    Format chunks into a context string for the AI.
    
    Args:
        chunks: List of document chunks
        
    Returns:
        str: Formatted context string
    """
    try:
        if not chunks:
            return ""
            
        formatted_chunks = []
        
        for chunk in chunks:
            raw_text = chunk.get("raw_text", "").strip()
            if not raw_text:
                continue
                
            # Extract metadata for source attribution
            metadata = chunk.get("metadata", {})
            document_id = metadata.get("document_id", "Unknown")
            source = metadata.get("source", "Unknown Source")
            
            # Format the chunk with source information
            formatted_chunk = f"--- From: {source} (ID: {document_id}) ---\n{raw_text}"
            formatted_chunks.append(formatted_chunk)
        
        # Join all formatted chunks
        context = "\n\n".join(formatted_chunks)
        
        logger.info(f"Formatted {len(formatted_chunks)} chunks into context")
        return context
    except Exception as e:
        logger.error(f"Error in format_context_from_chunks: {str(e)}", exc_info=True)
        # Return raw text concatenation as fallback
        return "\n\n".join([c.get("raw_text", "") for c in chunks if c.get("raw_text")])

# Create backward compatibility wrappers

def get_context_for_project_v2(supabase, project_id: str, user_query: str, project_info: str = "") -> Tuple[str, int]:
    """
    New version of get_context_for_project that returns a tuple with context and chunk count.
    This will be the main implementation once we fully transition.
    """
    try:
        logger.info(f"Starting get_context_for_project for project_id={project_id}")
        
        # Generate multiple search queries for better retrieval
        search_queries = generate_search_queries(
            user_query, 
            num_queries=3,
            project_info=project_info
        )
        logger.info(f"Generated search queries: {search_queries}")
        
        # Fetch document chunks for each query
        all_chunks = []
        for query in search_queries:
            chunks = fetch_document_chunks(supabase, project_id, query)
            all_chunks.extend(chunks)
        
        # If we didn't get anything from our reformulated queries, try the original
        if not all_chunks:
            logger.info("Reformulated queries returned no results, trying original query")
            all_chunks = fetch_document_chunks(supabase, project_id, user_query)
        
        # If still no results, try a more general approach with synthesis query
        if not all_chunks:
            logger.info("Original query returned no results, trying synthesis query")
            synthesis_query = generate_synthesis_query(
                user_query,
                project_info=project_info
            )
            logger.info(f"Generated synthesis query: {synthesis_query}")
            all_chunks = fetch_document_chunks(supabase, project_id, synthesis_query)
        
        # If still no results, try without a search query to get any available documents
        if not all_chunks:
            logger.info("Synthesis query returned no results, fetching any available documents")
            all_chunks = fetch_all_document_chunks(supabase, project_id)
        
        # Log available chunks for debugging
        logger.info(f"Total chunks before ranking: {len(all_chunks)}")
        
        if not all_chunks:
            logger.warning(f"No document chunks found for project {project_id}")
            return "", 0
        
        # Rank chunks by relevance to the original query
        ranked_chunks = rank_chunks_by_relevance(all_chunks, user_query)
        
        # Select top chunks based on a max context size
        top_chunks, num_chunks_used = select_top_chunks(ranked_chunks)
        
        # Format context
        context = format_context_from_chunks(top_chunks)
        logger.info(f"Generated context using {num_chunks_used} chunks")
        
        return context, num_chunks_used
    except Exception as e:
        logger.error(f"Error in get_context_for_project_v2: {str(e)}", exc_info=True)
        return "", 0

def get_context_for_project_with_selected_documents_v2(
    supabase, project_id: str, document_ids: List[str], user_query: str, project_info: str = ""
) -> Tuple[str, int]:
    """
    New version of get_context_for_project_with_selected_documents that returns a tuple.
    This will be the main implementation once we fully transition.
    """
    try:
        logger.info(f"Starting get_context_for_project_with_selected_documents for project_id={project_id}")
        logger.info(f"Selected document_ids: {document_ids}")
        
        # Generate multiple search queries for better retrieval
        search_queries = generate_search_queries(
            user_query, 
            num_queries=3,
            project_info=project_info
        )
        logger.info(f"Generated search queries: {search_queries}")
        
        # Fetch document chunks for each query
        all_chunks = []
        for query in search_queries:
            chunks = fetch_document_chunks_from_selected_documents(
                supabase, project_id, document_ids, query
            )
            all_chunks.extend(chunks)
        
        # If we didn't get anything from our reformulated queries, try the original
        if not all_chunks:
            logger.info("Reformulated queries returned no results, trying original query")
            all_chunks = fetch_document_chunks_from_selected_documents(
                supabase, project_id, document_ids, user_query
            )
        
        # If still no results, try a more general approach with synthesis query
        if not all_chunks:
            logger.info("Original query returned no results, trying synthesis query")
            synthesis_query = generate_synthesis_query(
                user_query,
                project_info=project_info
            )
            logger.info(f"Generated synthesis query: {synthesis_query}")
            all_chunks = fetch_document_chunks_from_selected_documents(
                supabase, project_id, document_ids, synthesis_query
            )
        
        # If still no results, try fetching chunks from these documents without a search
        if not all_chunks:
            logger.info("Synthesis query returned no results, fetching chunks from selected documents without search")
            all_chunks = fetch_all_chunks_from_selected_documents(
                supabase, project_id, document_ids
            )
        
        # Log available chunks for debugging
        logger.info(f"Total chunks before ranking: {len(all_chunks)}")
        
        if not all_chunks:
            # Check if any of the selected documents actually exist in the database
            valid_doc_ids = []
            for doc_id in document_ids:
                doc_exists = check_document_exists(supabase, project_id, doc_id)
                if doc_exists:
                    valid_doc_ids.append(doc_id)
            
            if not valid_doc_ids:
                logger.warning(f"None of the selected documents {document_ids} exist for project {project_id}")
            else:
                logger.warning(f"No chunks found for valid documents {valid_doc_ids} in project {project_id}")
            
            return "", 0
        
        # Rank chunks by relevance to the original query
        ranked_chunks = rank_chunks_by_relevance(all_chunks, user_query)
        
        # Select top chunks based on a max context size
        top_chunks, num_chunks_used = select_top_chunks(ranked_chunks)
        
        # Format context
        context = format_context_from_chunks(top_chunks)
        logger.info(f"Generated context using {num_chunks_used} chunks")
        
        return context, num_chunks_used
    except Exception as e:
        logger.error(f"Error in get_context_for_project_with_selected_documents_v2: {str(e)}", exc_info=True)
        return "", 0

# Keep the original function signatures but have them call the new implementations internally
def get_context_for_project_intermediate(supabase, project_id: str, query: str, project_info: str = ""):
    """Intermediate version that takes the same parameters as v2 but returns only the context string."""
    context, _ = get_context_for_project_v2(supabase, project_id, query, project_info)
    return context

def get_context_for_project_with_selected_documents_intermediate(
    supabase, project_id: str, document_ids: List[str], query: str, project_info: str = ""
):
    """Intermediate version that takes the same parameters as v2 but returns only the context string."""
    context, _ = get_context_for_project_with_selected_documents_v2(supabase, project_id, document_ids, query, project_info)
    return context

def fetch_all_chunks_from_selected_documents(supabase, project_id: str, document_ids: List[str]) -> List[dict]:
    """
    Fetch all document chunks from selected documents without performing a search.
    
    Args:
        supabase: Supabase client instance
        project_id: ID of the project
        document_ids: List of document IDs to fetch from
        
    Returns:
        List[dict]: List of document chunks
    """
    try:
        logger.info(f"Fetching all chunks from selected documents {document_ids} in project {project_id}")
        
        # Retrieve all chunks for the project
        response = supabase.table("sources").select("*").eq("project_id", project_id).execute()
        
        if not response.data:
            logger.warning(f"No chunks found for project {project_id}")
            return []
            
        # Filter chunks by document_id
        filtered_chunks = []
        for chunk in response.data:
            metadata = chunk.get("metadata", {})
            document_id = metadata.get("document_id", "")
            source = metadata.get("source", "")
            
            # Log document information for debugging
            if document_id or source:
                logger.info(f"Found chunk with document_id: {document_id}, source: {source}")
            
            # Try different matching approaches
            is_match = False
            
            # Direct match
            if document_id and document_id in document_ids:
                is_match = True
                logger.info(f"Direct match with document_id: {document_id}")
            elif source and source in document_ids:
                is_match = True
                logger.info(f"Direct match with source: {source}")
            
            # Try partial matches for temporary files
            else:
                for selected_id in document_ids:
                    # Check for partial matches in both directions
                    if ((document_id and selected_id in document_id) or 
                        (source and selected_id in source) or
                        (document_id and document_id in selected_id)):
                        is_match = True
                        logger.info(f"Partial match: selected_id={selected_id}, document_id={document_id}")
                        break
                    # Check basename matching
                    elif document_id and os.path.basename(document_id) == os.path.basename(selected_id):
                        is_match = True
                        logger.info(f"Basename match: document_id={document_id}, selected_id={selected_id}")
                        break
            
            if is_match:
                filtered_chunks.append(chunk)
        
        logger.info(f"Fetched {len(filtered_chunks)} chunks from selected documents in project {project_id}")
        return filtered_chunks
    except Exception as e:
        logger.error(f"Error in fetch_all_chunks_from_selected_documents: {str(e)}", exc_info=True)
        return []

def check_document_exists(supabase, project_id: str, document_id: str) -> bool:
    """
    Check if a document exists in the database for a given project.
    
    Args:
        supabase: Supabase client instance
        project_id: ID of the project
        document_id: ID of the document to check
        
    Returns:
        bool: True if the document exists, False otherwise
    """
    try:
        # Query for chunks with this document_id in the project
        response = supabase.table("sources").select("count").eq("project_id", project_id).execute()
        
        if not response.data or response.data[0].get("count", 0) == 0:
            return False
            
        # Check if any document matches the document_id
        for chunk in response.data:
            metadata = chunk.get("metadata", {})
            chunk_doc_id = metadata.get("document_id", "")
            source = metadata.get("source", "")
            
            # Direct match
            if (chunk_doc_id and chunk_doc_id == document_id) or (source and source == document_id):
                return True
                
            # Partial match for temporary filenames
            if ((chunk_doc_id and document_id in chunk_doc_id) or 
                (source and document_id in source) or
                (chunk_doc_id and chunk_doc_id in document_id)):
                return True
                
            # Basename match
            if chunk_doc_id and os.path.basename(chunk_doc_id) == os.path.basename(document_id):
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error in check_document_exists: {str(e)}", exc_info=True)
        return False 