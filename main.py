from fastmcp import FastMCP
import random
import json

#Create the FastMCP server instance
mcp=FastMCP("Simple Calculator Server")

#Tools: Add tow numbers
@mcp.tool
def add(a:int, b:int) ->int:
    """Add two numbers together.
    
    Args:
        a:First number
        b:second number

    Returns:
        The sum of the two numbers.
    """
    return a + b

#Tool: Generate a random number
@mcp.tool
def random_number(min_value: int=1, max_value: int=100) -> int:
    """Generate a random number within a range.
    
    Args:
        min_value: Minimum value (default is 1)
        max_value: Maximum value (default is 100)

    Returns:
        A random integer between min_value and max_value.
    """
    return random.randint(min_value, max_value)

#Resource: Server information
@mcp.resource("info://server")
def server_info() ->str:
    """Get information about this server."""
    info={
        "name": "Simple Calculator Server",
        "version": "1.0.0",
        "description": "A basic MCP server with math tools",
        "tools": ["add", "random_number"],
        "author": "Subodh Kumar Sahu"
    }
    return json.dumps(info, indent=2)


#Start the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8080)