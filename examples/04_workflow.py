"""
Workflow Pipeline Example
=========================

This example shows how to create declarative multi-agent
workflows with stages, conditions, and error handling.
"""

import asyncio
from reasona import Conductor, Workflow


async def main():
    # Create specialized agents for each stage
    planner = Conductor(
        name="planner",
        model="openai/gpt-4o",
        instructions="""You are a project planner. Create detailed, 
        actionable plans with clear steps and milestones."""
    )
    
    executor = Conductor(
        name="executor",
        model="openai/gpt-4o",
        instructions="""You are a task executor. Take plans and 
        describe how you would execute each step in detail."""
    )
    
    reviewer = Conductor(
        name="reviewer",
        model="anthropic/claude-3-5-sonnet",
        instructions="""You are a quality reviewer. Evaluate work 
        for completeness, quality, and suggest improvements."""
    )
    
    # Create a workflow
    workflow = Workflow(name="project-pipeline")
    
    # Add stages to the workflow
    workflow.add_stage(
        name="planning",
        agent=planner,
        prompt_template="Create a detailed plan for: {input}",
        description="Generate project plan"
    )
    
    workflow.add_stage(
        name="execution",
        agent=executor,
        prompt_template="Execute this plan step by step:\n\n{planning}",
        description="Execute the plan"
    )
    
    workflow.add_stage(
        name="review",
        agent=reviewer,
        prompt_template="Review this work and provide feedback:\n\n{execution}",
        description="Review and provide feedback"
    )
    
    # Optional: Add a conditional stage
    workflow.add_stage(
        name="revision",
        agent=executor,
        prompt_template="Revise based on this feedback:\n\n{review}",
        description="Revise if needed",
        condition=lambda ctx: "needs improvement" in ctx.get("review", "").lower()
    )
    
    # Visualize the workflow
    print("=== Workflow Structure ===")
    print(workflow.visualize())
    print()
    
    # Run the workflow
    print("=== Running Workflow ===\n")
    result = await workflow.run(
        input="Build a simple REST API for a todo list application"
    )
    
    # Print results from each stage
    print("\n=== Stage Results ===")
    for stage_name, stage_result in result.items():
        if stage_name != "input":
            print(f"\n📌 {stage_name.upper()}:")
            print("-" * 40)
            # Truncate for display
            print(stage_result[:500] + "..." if len(stage_result) > 500 else stage_result)
    
    # Access execution history
    print("\n=== Execution History ===")
    for entry in workflow.history:
        print(f"  {entry['timestamp']}: {entry['stage']} - {entry['status']}")


async def conditional_workflow():
    """Workflow with conditional branching."""
    
    classifier = Conductor(
        name="classifier",
        model="openai/gpt-4o",
        instructions="Classify requests as 'technical' or 'business'."
    )
    
    tech_expert = Conductor(
        name="tech-expert",
        model="openai/gpt-4o",
        instructions="You are a technical expert."
    )
    
    business_expert = Conductor(
        name="business-expert",
        model="openai/gpt-4o",
        instructions="You are a business expert."
    )
    
    workflow = Workflow(name="conditional-flow")
    
    workflow.add_stage(
        name="classify",
        agent=classifier,
        prompt_template="Classify this request (respond with just 'technical' or 'business'): {input}"
    )
    
    workflow.add_stage(
        name="tech_response",
        agent=tech_expert,
        prompt_template="Provide technical guidance for: {input}",
        condition=lambda ctx: "technical" in ctx.get("classify", "").lower()
    )
    
    workflow.add_stage(
        name="business_response",
        agent=business_expert,
        prompt_template="Provide business guidance for: {input}",
        condition=lambda ctx: "business" in ctx.get("classify", "").lower()
    )
    
    print("=== Conditional Workflow ===\n")
    
    # Test with technical request
    result = await workflow.run(
        input="How should I optimize my database queries for better performance?"
    )
    print("Technical request result:", result.get("tech_response", result.get("business_response")))
    
    # Reset and test with business request
    workflow.reset()
    result = await workflow.run(
        input="What pricing strategy should I use for my SaaS product?"
    )
    print("\nBusiness request result:", result.get("business_response", result.get("tech_response")))


async def retry_workflow():
    """Workflow with retry logic."""
    
    agent = Conductor(
        name="worker",
        model="openai/gpt-4o",
        instructions="You are a helpful assistant."
    )
    
    workflow = Workflow(name="retry-flow")
    
    workflow.add_stage(
        name="process",
        agent=agent,
        prompt_template="Process this request: {input}",
        retries=3,  # Retry up to 3 times on failure
        timeout=30  # Timeout after 30 seconds
    )
    
    result = await workflow.run(input="Generate a creative story idea")
    print("Result with retry:", result["process"])


if __name__ == "__main__":
    print("Running workflow pipeline example...\n")
    asyncio.run(main())
    
    print("\n" + "=" * 50 + "\n")
    asyncio.run(conditional_workflow())
    
    print("\n" + "=" * 50 + "\n")
    asyncio.run(retry_workflow())
