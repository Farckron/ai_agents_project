"""
PRRequest model for managing pull request creation requests.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class RequestStatus(Enum):
    """Status enumeration for PR requests."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PRRequestOptions:
    """Options for PR request configuration."""
    branch_name: Optional[str] = None
    pr_title: Optional[str] = None
    pr_description: Optional[str] = None
    base_branch: str = "main"
    auto_merge: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PRRequestOptions':
        """Create options from dictionary."""
        return cls(**data)


@dataclass
class PRRequest:
    """Model for PR creation requests."""
    user_request: str
    repo_url: str
    options: PRRequestOptions = field(default_factory=PRRequestOptions)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    pr_url: Optional[str] = None
    
    def update_status(self, status: RequestStatus, error_message: Optional[str] = None):
        """Update request status and timestamp."""
        self.status = status
        self.updated_at = datetime.now()
        if error_message:
            self.error_message = error_message
    
    def mark_completed(self, pr_url: str):
        """Mark request as completed with PR URL."""
        self.status = RequestStatus.COMPLETED
        self.pr_url = pr_url
        self.updated_at = datetime.now()
    
    def mark_failed(self, error_message: str):
        """Mark request as failed with error message."""
        self.status = RequestStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PR request to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PRRequest':
        """Create PR request from dictionary."""
        # Convert datetime strings back to datetime objects
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Convert status string to enum
        if isinstance(data.get('status'), str):
            data['status'] = RequestStatus(data['status'])
        
        # Convert options dict to PRRequestOptions
        if isinstance(data.get('options'), dict):
            data['options'] = PRRequestOptions.from_dict(data['options'])
        
        return cls(**data)
    
    def is_active(self) -> bool:
        """Check if request is currently active (pending or processing)."""
        return self.status in [RequestStatus.PENDING, RequestStatus.PROCESSING]
    
    def is_completed(self) -> bool:
        """Check if request is completed successfully."""
        return self.status == RequestStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if request has failed."""
        return self.status == RequestStatus.FAILED