#!/usr/bin/env python
"""
Supabase Schema Analysis Tool

This script examines the Supabase database schema, focusing on tables and functions
related to vectors and embeddings to help troubleshoot embedding dimension issues.
"""

import sys
import os
import pprint
from typing import Dict, Any, List

# Add parent directory to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app.core.database import supabase

def _print_banner(text: str):
    """Print a banner for better readability"""
    line = "=" * 80
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")

def get_table_structure(table_name: str) -> Dict[str, Any]:
    """
    Get the structure of a specific table
    
    Args:
        table_name: Name of the table to analyze
        
    Returns:
        Dict with table structure information
    """
    try:
        # Get table information using PostgreSQL's information_schema
        response = supabase.rpc(
            "exec_sql", 
            {
                "query": f"""
                SELECT column_name, data_type, character_maximum_length, 
                       is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
                """
            }
        ).execute()
        
        if not response.data:
            return {"status": "error", "message": f"No columns found for table '{table_name}'"}
            
        return {
            "status": "success",
            "table_name": table_name,
            "columns": response.data
        }
    except Exception as e:
        return {"status": "error", "message": f"Error getting table structure: {str(e)}"}

def get_sql_functions() -> Dict[str, Any]:
    """
    Get list of SQL functions in the database, focusing on vector-related functions
    
    Returns:
        Dict with function information
    """
    try:
        # Get function information
        response = supabase.rpc(
            "exec_sql", 
            {
                "query": """
                SELECT routine_name, routine_type, data_type, external_language,
                       routine_definition
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                ORDER BY routine_name
                """
            }
        ).execute()
        
        if not response.data:
            return {"status": "error", "message": "No functions found"}
            
        # Filter for potentially vector-related functions
        vector_keywords = ['vector', 'embedding', 'similarity', 'match', 'search']
        vector_functions = []
        
        for func in response.data:
            function_name = func.get('routine_name', '').lower()
            function_def = func.get('routine_definition', '').lower()
            
            # Check if function name or definition contains any vector keywords
            if any(keyword in function_name for keyword in vector_keywords) or \
               any(keyword in function_def for keyword in vector_keywords):
                vector_functions.append(func)
        
        return {
            "status": "success",
            "total_functions": len(response.data),
            "vector_functions": len(vector_functions),
            "functions": vector_functions
        }
    except Exception as e:
        return {"status": "error", "message": f"Error getting SQL functions: {str(e)}"}

def get_function_definition(function_name: str) -> Dict[str, Any]:
    """
    Get the definition of a specific SQL function
    
    Args:
        function_name: Name of the function to analyze
        
    Returns:
        Dict with function definition
    """
    try:
        # Get function definition
        response = supabase.rpc(
            "exec_sql", 
            {
                "query": f"""
                SELECT pg_get_functiondef(p.oid)
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'public' AND p.proname = '{function_name}'
                """
            }
        ).execute()
        
        if not response.data:
            return {"status": "error", "message": f"Function '{function_name}' not found"}
            
        return {
            "status": "success",
            "function_name": function_name,
            "definition": response.data[0]['pg_get_functiondef']
        }
    except Exception as e:
        return {"status": "error", "message": f"Error getting function definition: {str(e)}"}

def analyze_vector_dimensions() -> Dict[str, Any]:
    """
    Analyze dimensions of vectors in the database
    
    Returns:
        Dict with vector dimension information
    """
    try:
        # Get sample of vector dimensions from the sources table
        response = supabase.rpc(
            "exec_sql", 
            {
                "query": """
                SELECT chunk_id, 
                       CASE 
                           WHEN embedding IS NULL THEN NULL
                           WHEN typeof(embedding) = 'array' THEN array_length(embedding, 1)
                           ELSE -1  -- Not an array
                       END as embedding_dimension
                FROM sources
                LIMIT 100
                """
            }
        ).execute()
        
        if not response.data:
            return {"status": "error", "message": "No sources found"}
            
        # Analyze dimensions
        dimensions = {}
        not_array = 0
        null_embeddings = 0
        
        for row in response.data:
            dim = row.get('embedding_dimension')
            if dim is None:
                null_embeddings += 1
            elif dim == -1:
                not_array += 1
            else:
                dimensions[dim] = dimensions.get(dim, 0) + 1
        
        return {
            "status": "success",
            "total_sampled": len(response.data),
            "null_embeddings": null_embeddings,
            "not_array": not_array,
            "dimension_counts": dimensions
        }
    except Exception as e:
        return {"status": "error", "message": f"Error analyzing vector dimensions: {str(e)}"}

def get_extensions() -> Dict[str, Any]:
    """
    Get list of installed PostgreSQL extensions
    
    Returns:
        Dict with extension information
    """
    try:
        response = supabase.rpc(
            "exec_sql", 
            {
                "query": """
                SELECT name, default_version, installed_version, comment
                FROM pg_available_extensions
                WHERE installed_version IS NOT NULL
                ORDER BY name
                """
            }
        ).execute()
        
        if not response.data:
            return {"status": "error", "message": "No extensions found"}
            
        return {
            "status": "success",
            "extensions": response.data
        }
    except Exception as e:
        return {"status": "error", "message": f"Error getting extensions: {str(e)}"}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Supabase database schema for embedding/vector operations')
    parser.add_argument('--function', type=str, help='Get definition for a specific SQL function')
    parser.add_argument('--table', type=str, help='Get structure for a specific table')
    parser.add_argument('--full-definitions', action='store_true', help='Show full SQL function definitions')
    
    args = parser.parse_args()
    
    if args.function:
        # Get definition for a specific function
        _print_banner(f"Function Definition: {args.function}")
        func_def = get_function_definition(args.function)
        
        if func_def["status"] == "success":
            print(func_def["definition"])
        else:
            print(f"Error: {func_def['message']}")
    elif args.table:
        # Get structure for a specific table
        _print_banner(f"Table Structure: {args.table}")
        table_struct = get_table_structure(args.table)
        
        if table_struct["status"] == "success":
            for column in table_struct["columns"]:
                print(f"{column['column_name']}: {column['data_type']}" + 
                      (f"({column['character_maximum_length']})" if column['character_maximum_length'] else ""))
        else:
            print(f"Error: {table_struct['message']}")
    else:
        # Run all analyses
        _print_banner("Database Extensions")
        extensions = get_extensions()
        if extensions["status"] == "success":
            for ext in extensions["extensions"]:
                print(f"{ext['name']} (v{ext['installed_version']})")
        else:
            print(f"Error: {extensions['message']}")
        
        _print_banner("Sources Table Structure")
        sources_struct = get_table_structure("sources")
        if sources_struct["status"] == "success":
            for column in sources_struct["columns"]:
                print(f"{column['column_name']}: {column['data_type']}" + 
                      (f"({column['character_maximum_length']})" if column['character_maximum_length'] else ""))
        else:
            print(f"Error: {sources_struct['message']}")
        
        _print_banner("Vector Dimensions Analysis")
        dimensions = analyze_vector_dimensions()
        if dimensions["status"] == "success":
            print(f"Total records sampled: {dimensions['total_sampled']}")
            print(f"Null embeddings: {dimensions['null_embeddings']}")
            print(f"Non-array embeddings: {dimensions['not_array']}")
            print("\nDimension counts:")
            for dim, count in sorted(dimensions['dimension_counts'].items()):
                print(f"  {dim} dimensions: {count} records")
        else:
            print(f"Error: {dimensions['message']}")
        
        _print_banner("Vector-Related SQL Functions")
        functions = get_sql_functions()
        if functions["status"] == "success":
            print(f"Total functions: {functions['total_functions']}")
            print(f"Vector-related functions: {functions['vector_functions']}")
            print("\nFunctions:")
            for func in functions["functions"]:
                print(f"\n{func['routine_name']} ({func['data_type']})")
                if args.full_definitions:
                    print("Definition:")
                    print(func['routine_definition'])
        else:
            print(f"Error: {functions['message']}")
        
        _print_banner("Analysis Complete")
        print("To see more details about a specific function:")
        print("  python analyze_db_schema.py --function <function_name>")
        print("\nTo see details about a specific table:")
        print("  python analyze_db_schema.py --table <table_name>") 