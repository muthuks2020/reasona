"""
HyperMCP Server Example
=======================

This example shows how to create an MCP (Model Context Protocol)
server using HyperMCP that can be used with Claude Desktop and
other MCP clients.
"""

import asyncio
from typing import Optional
from reasona.mcp import HyperMCP, get_token


# Create the MCP server
mcp = HyperMCP(
    name="example-tools",
    version="1.0.0",
    description="Example MCP server with various tools"
)


# Define tools using decorators
@mcp.tool(description="Get current weather for a location")
async def get_weather(
    location: str,
    units: str = "celsius"
) -> dict:
    """
    Get the current weather for a location.
    
    Args:
        location: City name or coordinates
        units: Temperature units (celsius or fahrenheit)
    """
    # Simulated weather data
    return {
        "location": location,
        "temperature": 22 if units == "celsius" else 72,
        "units": units,
        "condition": "sunny",
        "humidity": 45,
        "wind_speed": 12
    }


@mcp.tool(description="Search for products in the catalog")
async def search_products(
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None
) -> list:
    """
    Search the product catalog.
    
    Args:
        query: Search query
        category: Optional category filter
        max_price: Optional maximum price filter
    """
    products = [
        {"id": 1, "name": "Laptop Pro", "category": "electronics", "price": 999.99},
        {"id": 2, "name": "Wireless Mouse", "category": "electronics", "price": 29.99},
        {"id": 3, "name": "Coffee Maker", "category": "appliances", "price": 79.99},
        {"id": 4, "name": "Standing Desk", "category": "furniture", "price": 449.99},
    ]
    
    # Filter products
    results = products
    if category:
        results = [p for p in results if p["category"] == category]
    if max_price:
        results = [p for p in results if p["price"] <= max_price]
    if query:
        results = [p for p in results if query.lower() in p["name"].lower()]
    
    return results


@mcp.tool(description="Calculate shipping cost")
async def calculate_shipping(
    weight_kg: float,
    destination: str,
    express: bool = False
) -> dict:
    """
    Calculate shipping cost for an order.
    
    Args:
        weight_kg: Package weight in kilograms
        destination: Destination country
        express: Whether to use express shipping
    """
    base_rate = 5.0
    weight_rate = weight_kg * 2.0
    express_multiplier = 2.5 if express else 1.0
    
    # International shipping costs more
    international = destination.lower() != "usa"
    international_fee = 15.0 if international else 0.0
    
    total = (base_rate + weight_rate + international_fee) * express_multiplier
    
    return {
        "weight_kg": weight_kg,
        "destination": destination,
        "express": express,
        "base_cost": base_rate,
        "weight_cost": weight_rate,
        "international_fee": international_fee,
        "total_cost": round(total, 2),
        "currency": "USD",
        "estimated_days": 2 if express else 7
    }


# Define resources
@mcp.resource(uri="config://app/settings", description="Application settings")
async def get_settings() -> dict:
    """Get application configuration settings."""
    return {
        "app_name": "Example App",
        "version": "1.0.0",
        "debug": False,
        "max_items_per_page": 50,
        "supported_currencies": ["USD", "EUR", "GBP"]
    }


@mcp.resource(uri="data://users/{user_id}", description="User profile data")
async def get_user(user_id: str) -> dict:
    """Get user profile by ID."""
    # Simulated user data
    users = {
        "1": {"id": "1", "name": "Alice", "email": "alice@example.com"},
        "2": {"id": "2", "name": "Bob", "email": "bob@example.com"},
    }
    return users.get(user_id, {"error": "User not found"})


# Define prompts (prompt templates)
@mcp.prompt(name="greeting", description="Generate a greeting message")
async def greeting_prompt(name: str, formal: bool = False) -> str:
    """Generate a greeting prompt."""
    if formal:
        return f"Please compose a formal greeting for {name}, suitable for a business context."
    return f"Create a friendly, casual greeting for {name}."


@mcp.prompt(name="product_description", description="Generate product description")
async def product_description_prompt(
    product_name: str,
    features: str,
    target_audience: str
) -> str:
    """Generate a product description prompt."""
    return f"""Write a compelling product description for:

Product: {product_name}
Key Features: {features}
Target Audience: {target_audience}

The description should be engaging, highlight benefits, and appeal to the target audience."""


# Authentication example
@mcp.tool(description="Get user's private data (requires auth)")
async def get_private_data() -> dict:
    """
    Get private user data. Requires authentication.
    """
    # Get the authentication token from context
    token = get_token()
    
    if not token:
        return {"error": "Authentication required"}
    
    # In a real implementation, validate the token
    if token == "valid-token":
        return {
            "user_id": "123",
            "private_notes": "This is private data",
            "api_usage": 42
        }
    
    return {"error": "Invalid token"}


def main():
    """Run the MCP server."""
    print("Starting HyperMCP server...")
    print()
    print("Server will be available at: http://localhost:9000")
    print()
    print("Endpoints:")
    print("  GET  /              - Server info")
    print("  GET  /tools         - List all tools")
    print("  POST /tools/{name}  - Execute a tool")
    print("  GET  /resources     - List all resources")
    print("  GET  /resources/{uri} - Read a resource")
    print("  GET  /prompts       - List all prompts")
    print("  POST /prompts/{name} - Get a prompt")
    print("  POST /rpc           - JSON-RPC 2.0 endpoint")
    print()
    print("To use with Claude Desktop, add to your config:")
    print('''
{
  "mcpServers": {
    "example-tools": {
      "url": "http://localhost:9000"
    }
  }
}
''')
    
    mcp.serve(host="0.0.0.0", port=9000)


if __name__ == "__main__":
    main()
