"""
PRWorkflow model for managing the PR creation workflow process.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class StepStatus(Enum):
    """Status enumeration for workflow steps."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class CompletionStatus(Enum):
    """Overall completion status for workflow."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    """Individual step in the PR workflow."""
    step_name: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def mark_completed(self, result: Optional[Dict[str, Any]] = None):
        """Mark step as completed with optional result."""
        self.status = StepStatus.COMPLETED
        self.result = result or {}
        self.timestamp = datetime.now()
    
    def mark_failed(self, error_message: str):
        """Mark step as failed with error message."""
        self.status = StepStatus.FAILED
        self.error_message = error_message
        self.timestamp = datetime.now()
    
    def is_completed(self) -> bool:
        """Check if step is completed."""
        return self.status == StepStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if step has failed."""
        return self.status == StepStatus.FAILED
    
    def is_pending(self) -> bool:
        """Check if step is pending."""
        return self.status == StepStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """Create step from dictionary."""
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data.get('status'), str):
            data['status'] = StepStatus(data['status'])
        return cls(**data)


@dataclass
class PRWorkflow:
    """Model for managing PR creation workflow."""
    request_id: str
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    steps: List[WorkflowStep] = field(default_factory=list)
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    completion_status: CompletionStatus = CompletionStatus.SUCCESS
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_step(self, step_name: str) -> WorkflowStep:
        """Add a new step to the workflow."""
        step = WorkflowStep(step_name=step_name)
        self.steps.append(step)
        return step
    
    def get_step(self, step_name: str) -> Optional[WorkflowStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.step_name == step_name:
                return step
        return None
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current (first pending) step."""
        for step in self.steps:
            if step.is_pending():
                return step
        return None
    
    def complete_step(self, step_name: str, result: Optional[Dict[str, Any]] = None):
        """Complete a specific step."""
        step = self.get_step(step_name)
        if step:
            step.mark_completed(result)
    
    def fail_step(self, step_name: str, error_message: str):
        """Fail a specific step."""
        step = self.get_step(step_name)
        if step:
            step.mark_failed(error_message)
    
    def get_completed_steps(self) -> List[WorkflowStep]:
        """Get all completed steps."""
        return [step for step in self.steps if step.is_completed()]
    
    def get_failed_steps(self) -> List[WorkflowStep]:
        """Get all failed steps."""
        return [step for step in self.steps if step.is_failed()]
    
    def get_pending_steps(self) -> List[WorkflowStep]:
        """Get all pending steps."""
        return [step for step in self.steps if step.is_pending()]
    
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.completed_at is not None
    
    def has_failed_steps(self) -> bool:
        """Check if workflow has any failed steps."""
        return len(self.get_failed_steps()) > 0
    
    def calculate_progress(self) -> float:
        """Calculate workflow progress as percentage."""
        if not self.steps:
            return 0.0
        completed = len(self.get_completed_steps())
        total = len(self.steps)
        return (completed / total) * 100.0
    
    def complete_workflow(self, pr_url: Optional[str] = None):
        """Mark workflow as completed."""
        self.completed_at = datetime.now()
        if pr_url:
            self.pr_url = pr_url
        
        # Determine completion status based on failed steps
        failed_steps = self.get_failed_steps()
        if not failed_steps:
            self.completion_status = CompletionStatus.SUCCESS
        elif len(failed_steps) < len(self.steps):
            self.completion_status = CompletionStatus.PARTIAL
        else:
            self.completion_status = CompletionStatus.FAILED
    
    def set_branch_name(self, branch_name: str):
        """Set the branch name for the workflow."""
        self.branch_name = branch_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        data = asdict(self)
        data['completion_status'] = self.completion_status.value
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        data['steps'] = [step.to_dict() for step in self.steps]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PRWorkflow':
        """Create workflow from dictionary."""
        # Convert datetime strings back to datetime objects
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('completed_at'), str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        # Convert completion status string to enum
        if isinstance(data.get('completion_status'), str):
            data['completion_status'] = CompletionStatus(data['completion_status'])
        
        # Convert steps list to WorkflowStep objects
        if isinstance(data.get('steps'), list):
            data['steps'] = [WorkflowStep.from_dict(step_data) for step_data in data['steps']]
        
        return cls(**data)
    
    @classmethod
    def create_standard_workflow(cls, request_id: str) -> 'PRWorkflow':
        """Create a workflow with standard PR creation steps."""
        workflow = cls(request_id=request_id)
        
        # Add standard workflow steps
        workflow.add_step("analyze_repository")
        workflow.add_step("generate_changes")
        workflow.add_step("validate_changes")
        workflow.add_step("create_branch")
        workflow.add_step("commit_changes")
        workflow.add_step("create_pull_request")
        
        return workflow