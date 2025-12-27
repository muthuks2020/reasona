"""
Workflow - Declarative multi-agent pipelines for Reasona.

Workflows allow you to define complex agent pipelines with
stages, conditions, and data flow between agents.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class StageStatus(str, Enum):
    """Status of a workflow stage."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result from a workflow stage execution."""
    
    stage_name: str
    status: StageStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Stage:
    """A single stage in a workflow pipeline."""
    
    name: str
    agent: Any  # Conductor instance
    prompt_template: Optional[str] = None
    condition: Optional[Callable[[dict[str, Any]], bool]] = None
    transform: Optional[Callable[[Any], Any]] = None
    timeout: Optional[float] = None
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class Workflow:
    """
    Declarative multi-agent workflow pipelines.
    
    Workflows allow you to define complex processing pipelines
    where multiple agents collaborate in a structured sequence.
    
    Example:
        >>> from reasona import Conductor, Workflow
        >>> 
        >>> planner = Conductor(name="planner", model="openai/gpt-4o")
        >>> executor = Conductor(name="executor", model="anthropic/claude-3-5-sonnet")
        >>> reviewer = Conductor(name="reviewer", model="google/gemini-2.0-flash")
        >>> 
        >>> workflow = Workflow(name="content-pipeline")
        >>> workflow.add_stage("plan", planner, "Create a plan for: {input}")
        >>> workflow.add_stage("execute", executor, "Execute this plan: {plan}")
        >>> workflow.add_stage("review", reviewer, "Review this content: {execute}")
        >>> 
        >>> result = await workflow.run("Write a blog about AI")
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        enable_logging: bool = True,
    ) -> None:
        """
        Initialize a new Workflow.
        
        Args:
            name: Name for this workflow.
            description: Optional description.
            enable_logging: Whether to log stage execution.
        """
        self.name = name
        self.description = description
        self.enable_logging = enable_logging
        
        # Workflow stages in order
        self._stages: list[Stage] = []
        
        # Stage lookup by name
        self._stage_map: dict[str, Stage] = {}
        
        # Execution history
        self._history: list[dict[str, Any]] = []
    
    def add_stage(
        self,
        name: str,
        agent: Any,
        prompt_template: Optional[str] = None,
        condition: Optional[Callable[[dict[str, Any]], bool]] = None,
        transform: Optional[Callable[[Any], Any]] = None,
        timeout: Optional[float] = None,
        retry_count: int = 0,
    ) -> "Workflow":
        """
        Add a stage to the workflow.
        
        Args:
            name: Unique stage name.
            agent: Conductor instance for this stage.
            prompt_template: Template string with {variable} placeholders.
            condition: Optional condition function to determine if stage runs.
            transform: Optional function to transform stage output.
            timeout: Optional timeout in seconds.
            retry_count: Number of retries on failure.
            
        Returns:
            Self for method chaining.
        """
        stage = Stage(
            name=name,
            agent=agent,
            prompt_template=prompt_template,
            condition=condition,
            transform=transform,
            timeout=timeout,
            retry_count=retry_count,
        )
        
        self._stages.append(stage)
        self._stage_map[name] = stage
        
        return self
    
    def remove_stage(self, name: str) -> "Workflow":
        """
        Remove a stage from the workflow.
        
        Args:
            name: Name of the stage to remove.
            
        Returns:
            Self for method chaining.
        """
        if name in self._stage_map:
            stage = self._stage_map[name]
            self._stages.remove(stage)
            del self._stage_map[name]
        
        return self
    
    def _build_prompt(
        self,
        template: Optional[str],
        context: dict[str, Any],
        default_input: str,
    ) -> str:
        """Build prompt from template and context."""
        if not template:
            # Use previous stage output or default input
            if context.get("_last_output"):
                return str(context["_last_output"])
            return default_input
        
        # Replace placeholders
        prompt = template
        for key, value in context.items():
            if not key.startswith("_"):
                prompt = prompt.replace(f"{{{key}}}", str(value))
        
        return prompt
    
    async def _execute_stage(
        self,
        stage: Stage,
        context: dict[str, Any],
        input_text: str,
    ) -> StageResult:
        """Execute a single workflow stage."""
        start_time = datetime.utcnow()
        
        try:
            # Check condition
            if stage.condition and not stage.condition(context):
                return StageResult(
                    stage_name=stage.name,
                    status=StageStatus.SKIPPED,
                    duration_ms=0.0,
                )
            
            # Build prompt
            prompt = self._build_prompt(stage.prompt_template, context, input_text)
            
            if self.enable_logging:
                print(f"[Workflow] Running stage: {stage.name}")
            
            # Execute with optional timeout
            if stage.timeout:
                output = await asyncio.wait_for(
                    stage.agent.athink(prompt),
                    timeout=stage.timeout,
                )
            else:
                output = await stage.agent.athink(prompt)
            
            # Apply transform if provided
            if stage.transform:
                output = stage.transform(output)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return StageResult(
                stage_name=stage.name,
                status=StageStatus.COMPLETED,
                output=output,
                duration_ms=duration,
            )
            
        except asyncio.TimeoutError:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return StageResult(
                stage_name=stage.name,
                status=StageStatus.FAILED,
                error="Stage timeout",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return StageResult(
                stage_name=stage.name,
                status=StageStatus.FAILED,
                error=str(e),
                duration_ms=duration,
            )
    
    async def run(
        self,
        input: str,
        initial_context: Optional[dict[str, Any]] = None,
        stop_on_error: bool = True,
    ) -> dict[str, Any]:
        """
        Execute the workflow pipeline.
        
        Args:
            input: Initial input to the workflow.
            initial_context: Optional initial context variables.
            stop_on_error: Whether to stop on stage failure.
            
        Returns:
            Dictionary with workflow results and stage outputs.
        """
        run_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Initialize context
        context: dict[str, Any] = {
            "input": input,
            "_run_id": run_id,
            "_last_output": None,
            **(initial_context or {}),
        }
        
        results: list[StageResult] = []
        
        if self.enable_logging:
            print(f"[Workflow] Starting: {self.name} (run_id={run_id[:8]})")
        
        # Execute stages in order
        for stage in self._stages:
            result = await self._execute_stage(stage, context, input)
            results.append(result)
            
            if result.status == StageStatus.COMPLETED:
                # Update context with stage output
                context[stage.name] = result.output
                context["_last_output"] = result.output
                
            elif result.status == StageStatus.FAILED and stop_on_error:
                if self.enable_logging:
                    print(f"[Workflow] Failed at stage: {stage.name}")
                break
        
        # Calculate total duration
        total_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Determine overall status
        failed_stages = [r for r in results if r.status == StageStatus.FAILED]
        overall_status = "failed" if failed_stages else "completed"
        
        # Store in history
        execution_record = {
            "run_id": run_id,
            "status": overall_status,
            "input": input,
            "output": context.get("_last_output"),
            "stages": [
                {
                    "name": r.stage_name,
                    "status": r.status.value,
                    "output": r.output,
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                }
                for r in results
            ],
            "total_duration_ms": total_duration,
            "timestamp": start_time.isoformat(),
        }
        self._history.append(execution_record)
        
        if self.enable_logging:
            status_str = "✓" if overall_status == "completed" else "✗"
            print(f"[Workflow] {status_str} Completed in {total_duration:.0f}ms")
        
        return execution_record
    
    def __call__(self, input: str, **kwargs: Any) -> dict[str, Any]:
        """Synchronous execution of the workflow."""
        return asyncio.get_event_loop().run_until_complete(
            self.run(input, **kwargs)
        )
    
    @property
    def stages(self) -> list[str]:
        """Get list of stage names."""
        return [s.name for s in self._stages]
    
    @property
    def history(self) -> list[dict[str, Any]]:
        """Get execution history."""
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self._history.clear()
    
    def visualize(self) -> str:
        """Generate ASCII visualization of the workflow."""
        lines = [f"Workflow: {self.name}"]
        if self.description:
            lines.append(f"  {self.description}")
        lines.append("")
        
        for i, stage in enumerate(self._stages):
            connector = "──▶" if i < len(self._stages) - 1 else "──○"
            lines.append(f"  [{stage.name}] ({stage.agent.name}) {connector}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"Workflow(name='{self.name}', stages={len(self._stages)})"
