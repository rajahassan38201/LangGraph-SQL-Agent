import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDataBaseTool, ListSQLDatabaseTool

def setup_database():
    """
    Creates a SQLite database and an 'Employees' table, 
    then populates it with sample data if it's empty.
    """
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()
    
    # Create the table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Age INTEGER,
        Department TEXT,
        Salary REAL,
        Mobile TEXT,
        Email TEXT
    );
    """)
    
    # Check if table is empty before inserting
    cursor.execute("SELECT COUNT(*) FROM Employees")
    if cursor.fetchone()[0] == 0:
        print("Populating database with sample data...")
        sample_data = [
            ('Alice Smith', 30, 'Engineering', 90000, '555-0101', 'alice@example.com'),
            ('Bob Johnson', 45, 'Sales', 75000, '555-0102', 'bob@example.com'),
            ('Charlie Lee', 28, 'Marketing', 68000, '555-0103', 'charlie@example.com'),
            ('David Brown', 52, 'Engineering', 120000, '555-0104', 'david@example.com'),
            ('Eve Davis', 35, 'Sales', 82000, '555-0105', 'eve@example.com'),
            ('Frank White', 41, 'HR', 72000, '555-0106', 'frank@example.com'),
        ]
        cursor.executemany(
            "INSERT INTO Employees (Name, Age, Department, Salary, Mobile, Email) VALUES (?, ?, ?, ?, ?, ?)", 
            sample_data
        )
    
    conn.commit()
    conn.close()
    print("Database 'company.db' is ready.")

# --- Tool Creation ---

# Initialize the SQL Database connection
db = SQLDatabase.from_uri("sqlite:///company.db")

# Initialize the SQL tools
list_tables_tool = ListSQLDatabaseTool(db=db)
query_sql_tool = QuerySQLDataBaseTool(db=db)

# Define the list of tools for export

tools = [list_tables_tool, query_sql_tool]


