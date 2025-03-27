#!/usr/bin/env python
"""
Diagnostic script to verify that project_id is correctly set in the sources table.
This script checks for sources with NULL project_id and provides statistics.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Supabase client
from app.core.database import supabase
from app.core.config import logger

def verify_sources_project_id():
    """Verify if sources have project_id correctly set"""
    try:
        # Get all sources
        sources_response = supabase.table("sources").select("id, source_id, chunk_id, project_id").execute()
        sources = sources_response.data
        
        if not sources:
            logger.info("No sources found in the database.")
            return
        
        total_sources = len(sources)
        sources_with_project_id = sum(1 for s in sources if s.get("project_id") is not None)
        sources_without_project_id = total_sources - sources_with_project_id
        
        logger.info(f"Total sources: {total_sources}")
        logger.info(f"Sources with project_id: {sources_with_project_id}")
        logger.info(f"Sources without project_id: {sources_without_project_id}")
        
        # Group sources by source_id
        source_id_groups = {}
        for source in sources:
            source_id = source.get("source_id")
            if source_id not in source_id_groups:
                source_id_groups[source_id] = []
            source_id_groups[source_id].append(source)
        
        logger.info(f"Number of distinct source_id values: {len(source_id_groups)}")
        
        # Check if sources with the same source_id have different project_id values
        inconsistent_groups = {}
        for source_id, group in source_id_groups.items():
            project_ids = set(s.get("project_id") for s in group)
            if len(project_ids) > 1:
                inconsistent_groups[source_id] = project_ids
        
        if inconsistent_groups:
            logger.warning(f"Found {len(inconsistent_groups)} source_id groups with inconsistent project_id values:")
            for source_id, project_ids in inconsistent_groups.items():
                logger.warning(f"  source_id: {source_id}, project_ids: {project_ids}")
        else:
            logger.info("All source_id groups have consistent project_id values.")
        
        # Display the first 5 sources without project_id
        if sources_without_project_id > 0:
            null_sources = [s for s in sources if s.get("project_id") is None][:5]
            logger.info("Sample of sources without project_id:")
            for i, source in enumerate(null_sources):
                logger.info(f"  {i+1}. id: {source.get('id')}, source_id: {source.get('source_id')}")
        
        return {
            "total_sources": total_sources,
            "with_project_id": sources_with_project_id,
            "without_project_id": sources_without_project_id,
            "inconsistent_groups": len(inconsistent_groups)
        }
    
    except Exception as e:
        logger.error(f"Error verifying sources project_id: {e}")
        return None

def update_null_project_ids(project_id: int, source_id: str = None):
    """
    Update sources with NULL project_id to a specific project_id
    
    Args:
        project_id: The project ID to set
        source_id: Optional source_id to filter by. If None, all NULL project_id sources will be updated.
    
    Returns:
        Number of records updated
    """
    try:
        query = supabase.table("sources").update({"project_id": project_id})
        
        # Add filters
        if source_id:
            query = query.eq("source_id", source_id)
        
        # Only update records with NULL project_id
        query = query.is_("project_id", "null")
        
        # Execute the update
        response = query.execute()
        
        updated_count = len(response.data) if response.data else 0
        logger.info(f"Updated {updated_count} sources with project_id={project_id}")
        return updated_count
    
    except Exception as e:
        logger.error(f"Error updating NULL project_ids: {e}")
        return 0

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify and fix project_id in sources")
    parser.add_argument("--update", type=int, help="Update NULL project_id to specified project_id")
    parser.add_argument("--source_id", type=str, help="Filter by source_id when updating")
    args = parser.parse_args()
    
    # Run verification
    results = verify_sources_project_id()
    
    # Update if requested
    if args.update:
        if results and results.get("without_project_id") > 0:
            updated = update_null_project_ids(args.update, args.source_id)
            logger.info(f"Updated {updated} records with NULL project_id to project_id={args.update}")
            
            # Verify again after update
            logger.info("Verifying after update:")
            verify_sources_project_id()
        else:
            logger.info("No sources with NULL project_id found. No update needed.") 