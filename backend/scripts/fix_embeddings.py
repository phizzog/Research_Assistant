#!/usr/bin/env python
"""
Embedding Diagnosis and Fix Script

This script analyzes embeddings in the Supabase database and identifies/fixes issues.
It checks for:
1. Missing embeddings
2. Non-vector embeddings (like strings/text in embedding field)
3. Incorrectly sized embeddings

If issues are found, it regenerates the embeddings using the current embedding model.
"""

import sys
import os
import time
from typing import Dict, Any, List, Tuple

# Add parent directory to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app.core.database import supabase
from app.core.ai import generate_embeddings
from app.core.config import logger

def analyze_embeddings(project_id: int = None) -> Dict[str, Any]:
    """
    Analyze embeddings in the database and identify issues
    
    Args:
        project_id: Optional project ID to filter sources
    
    Returns:
        Dict with analysis results
    """
    try:
        # Set up query filters based on project_id
        if project_id is not None:
            print(f"Analyzing embeddings for project {project_id}...")
            response = supabase.table("sources").select("*").eq("project_id", project_id).execute()
        else:
            print("Analyzing all embeddings in the database...")
            response = supabase.table("sources").select("*").execute()
            
        if not response.data:
            print(f"No sources found for {'project ' + str(project_id) if project_id else 'any project'}")
            return {
                "status": "warning",
                "message": f"No sources found for {'project ' + str(project_id) if project_id else 'any project'}",
                "total": 0,
                "issues": 0
            }
            
        # Initialize counters
        total_sources = len(response.data)
        missing_embeddings = 0
        incorrect_type_embeddings = 0
        incorrect_size_embeddings = 0
        ok_embeddings = 0
        issues_by_source = {}
        
        # Expected embedding size from the model (Nomic Embed)
        expected_embedding_size = 768
        
        print(f"Found {total_sources} sources to analyze")
        
        # Process each source
        for idx, source in enumerate(response.data):
            if (idx + 1) % 10 == 0:
                print(f"Analyzed {idx + 1}/{total_sources} sources...")
                
            source_id = source.get('source_id', 'unknown')
            chunk_id = source.get('chunk_id', 'unknown')
            embedding = source.get('embedding')
            
            # Check if embedding exists
            if embedding is None:
                missing_embeddings += 1
                issues_by_source[chunk_id] = "Missing embedding"
                continue
                
            # Check embedding type
            if not isinstance(embedding, list):
                incorrect_type_embeddings += 1
                issues_by_source[chunk_id] = f"Incorrect type: {type(embedding).__name__}"
                continue
                
            # Check if embedding is valid size
            if len(embedding) != expected_embedding_size:
                incorrect_size_embeddings += 1
                issues_by_source[chunk_id] = f"Incorrect size: {len(embedding)} (expected: {expected_embedding_size})"
                continue
                
            # If we got here, the embedding is OK
            ok_embeddings += 1
        
        # Calculate totals
        total_issues = missing_embeddings + incorrect_type_embeddings + incorrect_size_embeddings
        
        return {
            "status": "success",
            "message": f"Analysis complete for {total_sources} sources",
            "total": total_sources,
            "ok": ok_embeddings,
            "issues": total_issues,
            "missing": missing_embeddings,
            "incorrect_type": incorrect_type_embeddings,
            "incorrect_size": incorrect_size_embeddings,
            "issues_by_source": issues_by_source
        }
        
    except Exception as e:
        print(f"Error analyzing embeddings: {str(e)}")
        return {
            "status": "error",
            "message": f"Error analyzing embeddings: {str(e)}",
            "total": 0,
            "issues": 0
        }

def fix_embeddings(project_id: int = None) -> Dict[str, Any]:
    """
    Fix embeddings that have issues in the database
    
    Args:
        project_id: Optional project ID to filter sources
    
    Returns:
        Dict with fix results
    """
    try:
        # First analyze to find issues
        analysis = analyze_embeddings(project_id)
        
        if analysis["status"] != "success" or analysis["issues"] == 0:
            return {
                "status": analysis["status"],
                "message": "No issues found, no fixes needed" if analysis["status"] == "success" else analysis["message"],
                "fixed": 0,
                "total": analysis.get("total", 0)
            }
            
        print(f"Found {analysis['issues']} issues out of {analysis['total']} sources")
        print(f"- Missing embeddings: {analysis['missing']}")
        print(f"- Incorrect type: {analysis['incorrect_type']}")
        print(f"- Incorrect size: {analysis['incorrect_size']}")
        
        # Set up query filters based on project_id
        if project_id is not None:
            response = supabase.table("sources").select("*").eq("project_id", project_id).execute()
        else:
            response = supabase.table("sources").select("*").execute()
            
        # Process each source
        total_sources = len(response.data)
        fixed_count = 0
        errors = 0
        
        for idx, source in enumerate(response.data):
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{total_sources} sources (fixed: {fixed_count}, errors: {errors})...")
                
            chunk_id = source.get('chunk_id')
            
            # Skip sources that don't have issues
            if chunk_id not in analysis["issues_by_source"]:
                continue
                
            # Get the raw text to regenerate the embedding
            raw_text = source.get('raw_text')
            
            if not raw_text:
                print(f"Source {chunk_id} has no raw_text, skipping")
                errors += 1
                continue
                
            try:
                # Generate new embedding
                new_embedding = generate_embeddings(raw_text)
                
                # Validate the new embedding
                if not isinstance(new_embedding, list) or len(new_embedding) != 768:
                    print(f"Generated invalid embedding for {chunk_id}: type={type(new_embedding)}, len={len(new_embedding) if isinstance(new_embedding, list) else 'N/A'}")
                    errors += 1
                    continue
                    
                # Update the source with new embedding
                update_response = supabase.table("sources").update({
                    "embedding": new_embedding
                }).eq("chunk_id", chunk_id).execute()
                
                if update_response.data:
                    fixed_count += 1
                else:
                    print(f"Failed to update embedding for source {chunk_id}")
                    errors += 1
            except Exception as e:
                print(f"Error fixing embedding for source {chunk_id}: {str(e)}")
                errors += 1
                
        return {
            "status": "success",
            "message": f"Fixed {fixed_count} embeddings out of {analysis['issues']} issues found",
            "total": total_sources,
            "issues_found": analysis["issues"],
            "fixed": fixed_count,
            "errors": errors
        }
        
    except Exception as e:
        print(f"Error fixing embeddings: {str(e)}")
        return {
            "status": "error",
            "message": f"Error fixing embeddings: {str(e)}",
            "fixed": 0
        }

def _print_banner(text: str):
    """Print a banner for better readability"""
    line = "=" * 80
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze and fix embeddings in the Supabase database')
    parser.add_argument('--project-id', type=int, help='Project ID to filter sources (optional)')
    parser.add_argument('--analysis-only', action='store_true', help='Only analyze, don\'t fix embeddings')
    
    args = parser.parse_args()
    
    _print_banner("Embedding Analysis and Fix Tool")
    
    # Run analysis
    analysis = analyze_embeddings(args.project_id)
    
    _print_banner("Analysis Results")
    for key, value in analysis.items():
        if key != "issues_by_source":  # Skip the detailed issues list for cleaner output
            print(f"{key}: {value}")
    
    # If there are issues and --analysis-only is not set, fix them
    if analysis["status"] == "success" and analysis["issues"] > 0 and not args.analysis_only:
        proceed = input("\nDo you want to proceed with fixing these issues? (y/n): ")
        
        if proceed.lower() in ("y", "yes"):
            _print_banner("Fixing Embeddings")
            
            fix_results = fix_embeddings(args.project_id)
            
            _print_banner("Fix Results")
            for key, value in fix_results.items():
                print(f"{key}: {value}")
        else:
            print("\nFix operation cancelled. No changes were made.")
    
    print("\nDone!") 