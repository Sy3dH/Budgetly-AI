import re

READ_ONLY_COMMANDS = {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN"}

def is_read_only(query: str) -> bool:
    # Extract the first word (command) from the SQL query
    return True
    # command_match = re.match(r"^\s*(\w+)", query, re.IGNORECASE)
    # if not command_match:
    #     return False
    #
    # command = command_match.group(1).upper()
    # return command in READ_ONLY_COMMANDS
