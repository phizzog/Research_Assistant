#!/usr/bin/env python
"""
Database Migration Script

This script runs SQL migrations on the Supabase database.
It reads SQL files from the scripts directory and executes them.

Usage:
    python run_migration.py --sql_file add_content_column.sql
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import supabase
from app.core.config import logger

def run_migration(sql_file: str):
    """Run a SQL migration file on the Supabase database"""
    try:
        # Get the full path to the SQL file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_path = os.path.join(script_dir, sql_file)
        
        # Check if the file exists
        if not os.path.exists(sql_path):
            logger.error(f"SQL file not found: {sql_path}")
            sys.exit(1)
        
        # Read the SQL file
        with open(sql_path, 'r') as f:
            sql = f.read()
        
        # Execute the SQL
        logger.info(f"Running SQL migration: {sql_file}")
        response = supabase.rpc("exec_sql", {"query": sql}).execute()
        
        # Check for errors
        if response.error:
            logger.error(f"Error running SQL migration: {response.error}")
            sys.exit(1)
        
        logger.info(f"SQL migration completed successfully: {sql_file}")
        
    except Exception as e:
        logger.error(f"Error running SQL migration: {str(e)}")
        sys.exit(1)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run SQL migrations on the Supabase database")
    parser.add_argument("--sql_file", required=True, help="SQL file to run")
    args = parser.parse_args()
    
    # Run the migration
    run_migration(args.sql_file)

if __name__ == "__main__":
    main() 