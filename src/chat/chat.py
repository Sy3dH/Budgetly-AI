import os
import logging
from dotenv import load_dotenv
from chat.db_config import get_db_connection
from chat.query_guard import is_read_only
from google import genai
import re

load_dotenv()
logging.basicConfig(filename="query.log", level=logging.INFO)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def extract_sql(text: str) -> str:
    """
    Extract and sanitize the SQL query from LLM output.
    Handles common markdown, explanations, and trims extra text.
    """
    if not text:
        return ""

    # Remove common markdown wrappers
    text = text.strip()

    # Match inside ```sql ... ``` or ```...```
    code_block = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if code_block:
        return code_block.group(1).strip()

    fallback_match = re.search(r"(SELECT|SHOW|DESCRIBE|EXPLAIN)\s.+", text, re.IGNORECASE | re.DOTALL)
    if fallback_match:
        return fallback_match.group(0).strip()

    return text


def get_table_schema():
    """Return the table schema information as a string"""
    return """
🔹 Table: accounts
  - accountId (bigint(20)) NOT NULL
  - accountIBAN (varchar(34)) NOT NULL
  - accountTyp (varchar(50)) NULL
  - accountCategory (varchar(50)) NULL
  - balance (varchar(50)) NOT NULL
  - currency (varchar(3)) NOT NULL

🔹 Table: categories
  - categoryId (bigint(20)) NOT NULL
  - categoryName (varchar(255)) NOT NULL
  - categoryType (varchar(50)) NULL
  - predefined (tinyint(1)) NULL

🔹 Table: subcategories
  - subCategoryId (bigint(20)) NOT NULL
  - categoryId (bigint(20)) NOT NULL
  - subCategoryName (varchar(255)) NOT NULL
  - urgency (varchar(50)) NULL
  - predefined (tinyint(1)) NULL

🔹 Table: transactions
  - transactionId (varchar(36)) NOT NULL
  - accountId (bigint(20)) NOT NULL
  - categoryId (bigint(20)) NOT NULL
  - subcategoryId (bigint(20)) NOT NULL
  - date (bigint(20)) NOT NULL
  - amount (varchar(50)) NOT NULL
  - type (varchar(50)) NULL
  - frequency (varchar(50)) NULL
  - currency (varchar(3)) NOT NULL
  - description (text) NULL
"""


def natural_language_to_sql(nl_query: str) -> str:
    schema = get_table_schema()
    prompt = f"""
You are a SQL assistant. Convert the following natural language request into a single secure MySQL query.
Avoid any destructive operations (no UPDATE, DELETE, INSERT, DROP, etc.). Here are the following tables and their detailed columns:

{schema}

Natural language: "{nl_query}"
Return only the SQL code.
"""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text.strip("`")  # remove markdown-style formatting


def format_query_results(results, cursor_description):
    """Format query results into a readable string with column headers"""
    if not results:
        return "No results found."

    # Get column names
    columns = [desc[0] for desc in cursor_description]

    # Create formatted output
    formatted_results = []
    formatted_results.append("Query Results:")
    formatted_results.append("-" * 50)

    # Add header
    header = " | ".join(columns)
    formatted_results.append(header)
    formatted_results.append("-" * len(header))

    # Add rows
    for row in results:
        row_str = " | ".join(str(value) if value is not None else "NULL" for value in row)
        formatted_results.append(row_str)

    return "\n".join(formatted_results)


def generate_natural_language_response(original_query: str, sql_query: str, query_results: str) -> str:
    """Generate a natural language response based on the query and its results"""
    schema = get_table_schema()

    prompt = f"""
You are a helpful financial assistant. A user asked a question about their financial data, and you executed a SQL query to get the answer.

Database Schema:
{schema}

User's Original Question: "{original_query}"

SQL Query Executed: {sql_query}

Query Results:
{query_results}

Please provide a clear, concise, and helpful natural language response to the user's original question based on the query results. 
If there are no results, explain that appropriately. 
Make the response conversational and easy to understand, avoiding technical jargon.
Focus on answering the user's question directly and highlight key insights from the data.
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text.strip()


def execute_safe_query(sql: str, original_query: str):
    if not is_read_only(sql):
        raise ValueError("Only read-only queries are allowed.")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SET SESSION max_execution_time=1000")

        logging.info(f"Executing query: {sql}")
        cursor.execute(sql)

        results = cursor.fetchall()

        # Format results for display and LLM processing
        formatted_results = format_query_results(results, cursor.description)
        print("Raw Results:")
        print(formatted_results)
        print("\n" + "=" * 60 + "\n")

        # Generate natural language response
        nl_response = generate_natural_language_response(original_query, sql, formatted_results)
        print("Natural Language Response:")
        print(nl_response)

        cursor.close()
        conn.close()

        return results, nl_response

    except Exception as e:
        logging.error(f"Error during DB execution: {e}")
        print(f"Database Error: {e}")
        return None, None


def main():
    nl_query = "What is the total expense of the Fuel?"

    print(f"User Question: {nl_query}")
    print("-" * 60)

    # Generate SQL
    sql = natural_language_to_sql(nl_query)
    print(f"Generated SQL:\n{sql}")
    print("-" * 60)

    # Clean and execute SQL
    cleaned_sql = extract_sql(sql)

    try:
        results, nl_response = execute_safe_query(cleaned_sql, nl_query)
    except ValueError as ve:
        print(f"❌ Rejected: {ve}")


if __name__ == "__main__":
    main()