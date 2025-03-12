from app.core.database import supabase
from app.core.ai import generate_embeddings
from app.models.schemas import ParserOutput
from app.core.config import logger
from typing import List

async def store_pdf_content(pdf_data: ParserOutput) -> int:
    """
    Store the parsed PDF content in Supabase for later retrieval.
    This function creates chunks of text and stores them with embeddings.
    
    Returns:
        int: Number of chunks stored
    """
    try:
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
        
        # Store each chunk with its embedding
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = generate_embeddings(chunk)
            
            # Store in Supabase
            supabase.table("chunks").insert({
                "content": chunk,
                "embedding": embedding,
                "metadata": {
                    "source": pdf_data.document.filename,
                    "chunk_index": i
                }
            }).execute()
        
        logger.info(f"Stored {len(chunks)} chunks from PDF {pdf_data.document.filename}")
        return len(chunks)
    except Exception as e:
        logger.error(f"Error storing PDF content: {e}")
        raise

def get_context_from_query(query: str, top_k: int = 5) -> str:
    """
    Retrieve context from Supabase based on query
    
    Args:
        query: The search query
        top_k: Number of chunks to retrieve
        
    Returns:
        str: Concatenated context
    """
    try:
        # Generate embedding for the query
        query_embedding = generate_embeddings(query)
        
        # Retrieve matching chunks
        chunks_data = supabase.rpc("match_chunks", {
            "query_embedding": query_embedding,
            "match_count": top_k
        }).execute()
        
        if not chunks_data.data:
            logger.warning("No matching chunks found")
            return ""
            
        # Extract and join the text from the chunks
        relevant_chunks = [item["contextualized_text"] for item in chunks_data.data]
        context = "\n\n".join(relevant_chunks)
        
        logger.info(f"Retrieved {len(relevant_chunks)} chunks for query: {query}")
        return context
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return "" 