"""
Workflow Pipeline Example

This example demonstrates creating declarative multi-agent workflows
with stages, conditions, and transforms.

Usage:
    python examples/workflow_pipeline.py

Requirements:
    - Set OPENAI_API_KEY environment variable
"""

import asyncio
from reasona import Conductor, Workflow
from reasona.tools import Calculator, DateTime, JsonParser


# Create agents for different stages
planner = Conductor(
    name="planner",
    model="openai/gpt-4o",
    instructions="""You are a project planner. Create detailed, actionable plans.
Output your plans in a structured format with numbered steps.""",
)

executor = Conductor(
    name="executor",
    model="openai/gpt-4o",
    instructions="""You are a task executor. Take plans and execute them step by step.
Report on what was accomplished at each step.""",
    tools=[Calculator(), DateTime()],
)

reviewer = Conductor(
    name="reviewer",
    model="openai/gpt-4o",
    instructions="""You are a quality reviewer. Review completed work and provide:
1. A quality score (1-10)
2. Key strengths
3. Areas for improvement
4. Final recommendation""",
)

summarizer = Conductor(
    name="summarizer",
    model="openai/gpt-4o",
    instructions="""You are a summarizer. Create concise executive summaries.
Focus on key outcomes, metrics, and actionable insights.""",
)


def create_content_workflow():
    """Create a content generation workflow."""
    workflow = Workflow(
        name="content-pipeline",
        description="Multi-stage content generation workflow"
    )
    
    # Stage 1: Planning
    workflow.add_stage(
        name="plan",
        agent=planner,
        prompt_template="""Create a detailed content plan for the following topic:

Topic: {input}

Include:
- Target audience
- Key messages (3-5)
- Content structure
- Estimated word count""",
        timeout=60.0,
    )
    
    # Stage 2: Content Creation
    workflow.add_stage(
        name="create",
        agent=executor,
        prompt_template="""Based on this content plan, create the actual content:

Plan:
{plan}

Write engaging, informative content following the plan structure.""",
        timeout=120.0,
    )
    
    # Stage 3: Review
    workflow.add_stage(
        name="review",
        agent=reviewer,
        prompt_template="""Review the following content:

{create}

Provide a detailed quality assessment.""",
        timeout=60.0,
    )
    
    # Stage 4: Final Summary
    workflow.add_stage(
        name="summarize",
        agent=summarizer,
        prompt_template="""Create an executive summary of this content project:

Original Topic: {input}
Content Created: {create}
Review: {review}

Summarize the key outcomes and quality metrics.""",
        timeout=30.0,
    )
    
    return workflow


def create_analysis_workflow():
    """Create a data analysis workflow."""
    workflow = Workflow(
        name="analysis-pipeline",
        description="Multi-stage data analysis workflow"
    )
    
    analyzer = Conductor(
        name="analyzer",
        model="openai/gpt-4o",
        instructions="You analyze data and identify patterns.",
        tools=[Calculator(), JsonParser()],
    )
    
    interpreter = Conductor(
        name="interpreter",
        model="openai/gpt-4o",
        instructions="You interpret analysis results and explain their significance.",
    )
    
    workflow.add_stage(
        name="analyze",
        agent=analyzer,
        prompt_template="Analyze this data and identify key patterns:\n\n{input}",
    )
    
    workflow.add_stage(
        name="interpret",
        agent=interpreter,
        prompt_template="Interpret these analysis results:\n\n{analyze}",
    )
    
    workflow.add_stage(
        name="recommend",
        agent=reviewer,
        prompt_template="Based on this interpretation, provide recommendations:\n\n{interpret}",
    )
    
    return workflow


async def run_workflow_demo():
    """Demonstrate workflow execution."""
    print("\n🔄 Workflow Pipeline Demo\n")
    print("=" * 60)
    
    # Create the workflow
    workflow = create_content_workflow()
    
    # Visualize the workflow
    print("📊 Workflow Structure:")
    print(workflow.visualize())
    print()
    
    # Define the input
    input_topic = "The impact of artificial intelligence on remote work productivity"
    
    print(f"📥 Input: {input_topic}\n")
    print("=" * 60)
    print("🚀 Starting workflow execution...\n")
    
    # Run the workflow
    # Note: This requires API keys to actually execute
    # result = await workflow.run(input_topic)
    
    print("💡 To run this workflow, ensure API keys are set and uncomment the run() call.")
    print("\nWorkflow stages:")
    for i, stage in enumerate(workflow.stages, 1):
        print(f"  {i}. {stage.name} ({stage.agent.name})")


async def run_conditional_workflow():
    """Demonstrate conditional workflow execution."""
    print("\n🔀 Conditional Workflow Demo\n")
    print("=" * 60)
    
    workflow = Workflow(name="conditional-pipeline")
    
    # Add stages with conditions
    workflow.add_stage(
        name="classify",
        agent=planner,
        prompt_template="Classify this request as 'simple' or 'complex': {input}",
    )
    
    # These stages would have conditions in a full implementation
    workflow.add_stage(
        name="simple_handler",
        agent=executor,
        prompt_template="Handle this simple request: {input}",
        condition=lambda ctx: "simple" in ctx.get("classify", "").lower(),
    )
    
    workflow.add_stage(
        name="complex_handler",
        agent=reviewer,
        prompt_template="Handle this complex request with full analysis: {input}",
        condition=lambda ctx: "complex" in ctx.get("classify", "").lower(),
    )
    
    print("📊 Conditional Workflow Structure:")
    print(workflow.visualize())


async def run_parallel_workflow():
    """Demonstrate parallel stage execution concept."""
    print("\n⚡ Parallel Execution Concept\n")
    print("=" * 60)
    
    # In a parallel workflow, multiple agents work simultaneously
    agents = [
        Conductor(name="researcher-1", model="openai/gpt-4o", instructions="Research topic A"),
        Conductor(name="researcher-2", model="openai/gpt-4o", instructions="Research topic B"),
        Conductor(name="researcher-3", model="openai/gpt-4o", instructions="Research topic C"),
    ]
    
    print("Parallel execution would run these agents simultaneously:")
    for agent in agents:
        print(f"  - {agent.name}")
    
    print("\nResults would be aggregated by a coordinator agent.")


async def main():
    """Run all workflow demos."""
    print("\n" + "=" * 60)
    print("    REASONA WORKFLOW PIPELINE EXAMPLES")
    print("=" * 60)
    
    await run_workflow_demo()
    await run_conditional_workflow()
    await run_parallel_workflow()
    
    print("\n" + "=" * 60)
    print("    Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
