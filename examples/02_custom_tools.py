"""
Custom Tools Example
====================

This example shows how to create custom tools for your agents
using both the class-based and decorator approaches.
"""

import asyncio
from typing import Optional

from reasona import Conductor
from reasona.tools import NeuralTool, tool, ToolRegistry


# Approach 1: Class-based tool
class WeatherTool(NeuralTool):
    """A tool that fetches weather information."""
    
    name = "get_weather"
    description = "Get the current weather for a location"
    
    async def execute(
        self,
        location: str,
        units: str = "celsius"
    ) -> dict:
        """
        Get weather for a location.
        
        Args:
            location: City name or coordinates
            units: Temperature units (celsius or fahrenheit)
            
        Returns:
            Weather data dictionary
        """
        # In a real implementation, this would call a weather API
        return {
            "location": location,
            "temperature": 22 if units == "celsius" else 72,
            "units": units,
            "condition": "sunny",
            "humidity": 45
        }


# Approach 2: Decorator-based tool
@tool(name="search_database", description="Search the product database")
async def search_database(
    query: str,
    limit: int = 10,
    category: Optional[str] = None
) -> list:
    """
    Search for products in the database.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        category: Optional category filter
        
    Returns:
        List of matching products
    """
    # Simulated database search
    products = [
        {"id": 1, "name": "Laptop Pro", "category": "electronics", "price": 999},
        {"id": 2, "name": "Wireless Mouse", "category": "electronics", "price": 49},
        {"id": 3, "name": "Coffee Maker", "category": "appliances", "price": 79},
    ]
    
    # Filter by category if specified
    if category:
        products = [p for p in products if p["category"] == category]
    
    # Simple search matching
    results = [p for p in products if query.lower() in p["name"].lower()]
    
    return results[:limit]


# Approach 3: Using ToolRegistry
registry = ToolRegistry()


@registry.register
@tool(name="send_email", description="Send an email message")
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None
) -> dict:
    """
    Send an email message.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        cc: Optional CC recipient
        
    Returns:
        Status of the email send operation
    """
    # Simulated email sending
    print(f"📧 Sending email to: {to}")
    print(f"   Subject: {subject}")
    print(f"   Body: {body[:50]}...")
    
    return {
        "status": "sent",
        "to": to,
        "message_id": "msg_123456"
    }


async def main():
    # Create an agent with custom tools
    agent = Conductor(
        name="tools-demo",
        model="openai/gpt-4o",
        instructions="""You are a helpful assistant with access to weather, 
        product search, and email tools. Use them when appropriate.""",
        tools=[
            WeatherTool(),
            search_database,  # Decorated function
            *registry.get_tools()  # Tools from registry
        ]
    )
    
    # Test weather tool
    print("=== Weather Query ===")
    response = await agent.athink("What's the weather like in Paris?")
    print(f"Response: {response}\n")
    
    # Test search tool
    print("=== Product Search ===")
    response = await agent.athink("Search for laptops in the database")
    print(f"Response: {response}\n")
    
    # Test email tool
    print("=== Send Email ===")
    response = await agent.athink(
        "Send an email to team@example.com with subject 'Meeting Tomorrow' "
        "and body 'Don't forget our 10am meeting!'"
    )
    print(f"Response: {response}\n")
    
    # List available tools
    print("=== Available Tools ===")
    for tool_obj in agent.tools:
        name = getattr(tool_obj, 'name', tool_obj.__class__.__name__)
        desc = getattr(tool_obj, 'description', 'No description')
        print(f"  - {name}: {desc}")


if __name__ == "__main__":
    asyncio.run(main())
