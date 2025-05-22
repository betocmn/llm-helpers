#!/usr/bin/env python3
"""
Generates a text representation of database structure and sample data for LLM prompts.

This script connects to a PostgreSQL database and outputs:
- A list of all tables in the current database
- For each table:
  - Full description of the columns (structure)
  - Example of the last 10 records ordered by modified_date column

Usage:
    python bin/print_db_info.py [options]

Example:
    python bin/print_db_info.py -H localhost -p 5432 -d mydb -U postgres -o db_info.txt
"""
import os
import sys
import argparse
import psycopg2
from psycopg2 import sql

def get_tables(cursor):
    """Get all tables in the current database."""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    return [row[0] for row in cursor.fetchall()]

def get_table_structure(cursor, table_name):
    """Get column definitions for a table."""
    cursor.execute("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    
    result = []
    for col_name, data_type, is_nullable, default in cursor.fetchall():
        nullable = "NOT NULL" if is_nullable == 'NO' else ""
        default_str = f"DEFAULT {default}" if default else ""
        result.append(f"{col_name} {data_type} {nullable} {default_str}".strip())
    
    return result

def get_table_sample(cursor, table_name, output):
    """Get sample rows from a table, ordered by modified_date if it exists."""
    # Check if modified_date column exists
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
          AND column_name = 'modified_date'
    """, (table_name,))
    
    has_modified_date = cursor.fetchone() is not None
    
    # Get column names for this table
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    
    columns = [row[0] for row in cursor.fetchall()]
    
    # Prepare the SQL query
    if has_modified_date:
        query = sql.SQL("""
            SELECT {columns}
            FROM {table}
            ORDER BY modified_date DESC
            LIMIT 10
        """).format(
            columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
            table=sql.Identifier(table_name)
        )
    else:
        # If no modified_date, just get the last 10 rows
        print(f"Note: Table '{table_name}' has no modified_date column. Showing 10 rows without ordering.", file=output)
        query = sql.SQL("""
            SELECT {columns}
            FROM {table}
            LIMIT 10
        """).format(
            columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
            table=sql.Identifier(table_name)
        )
    
    # Execute the query
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("No data found in this table.", file=output)
        return
    
    # Get column widths for formatting
    col_widths = []
    for i, col in enumerate(columns):
        # Get max width of column name and data
        col_width = max(
            len(str(col)),
            max(len(str(row[i])) for row in rows)
        )
        col_widths.append(col_width)
    
    # Print header
    header = " | ".join(f"{col:{width}}" for col, width in zip(columns, col_widths))
    separator = "-+-".join("-" * width for width in col_widths)
    print(f" {header} ", file=output)
    print(f"-{separator}-", file=output)
    
    # Print rows
    for row in rows:
        formatted_row = " | ".join(f"{str(val):{width}}" for val, width in zip(row, col_widths))
        print(f" {formatted_row} ", file=output)

def print_db_info(host, port, dbname, user, password, output_file=None):
    """
    Connect to database and print information about tables and their data.
    
    Args:
        host (str): Database host
        port (int): Database port
        dbname (str): Database name
        user (str): Database user
        password (str): Database password
        output_file (str): Path to output file (or None for stdout)
    """
    # Open output file if specified
    out = sys.stdout
    if output_file:
        out = open(output_file, 'w', encoding='utf-8')
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        
        with conn.cursor() as cursor:
            # Get all tables
            tables = get_tables(cursor)
            
            if not tables:
                print("No tables found in the database.", file=out)
                return
                
            # Process each table
            for table_name in tables:
                print(f"=========== TABLE: {table_name} ===========", file=out)
                
                # Print column structure
                print("COLUMNS:", file=out)
                for column_def in get_table_structure(cursor, table_name):
                    print(column_def, file=out)
                
                print("\nLAST 10 ROWS:", file=out)
                get_table_sample(cursor, table_name, out)
                
                # Add separator between tables
                print("\n\n", file=out)
                
    except psycopg2.Error as e:
        print(f"Database error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Close connection and output file if opened
        if 'conn' in locals():
            conn.close()
        if output_file and out != sys.stdout:
            out.close()

def main():
    parser = argparse.ArgumentParser(
        description="Generate database structure and sample data for LLM prompts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-H", "--host", 
        default="localhost",
        help="Database host"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=5432,
        help="Database port"
    )
    parser.add_argument(
        "-d", "--dbname", 
        required=True,
        help="Database name"
    )
    parser.add_argument(
        "-U", "--user", 
        required=True,
        help="Database user"
    )
    parser.add_argument(
        "-P", "--password",
        help="Database password (if not provided, will use environment variable PGPASSWORD)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: print to stdout)"
    )
    
    args = parser.parse_args()
    
    # Use environment variable for password if not provided
    password = args.password or os.environ.get('PGPASSWORD', '')
    
    # Generate database info
    print_db_info(
        args.host,
        args.port,
        args.dbname,
        args.user,
        password,
        args.output
    )

if __name__ == "__main__":
    main() 