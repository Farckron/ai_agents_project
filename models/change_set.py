"""
ChangeSet model for tracking individual file changes in PR requests.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class ChangeOperation(Enum):
    """Types of file operations."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class ValidationStatus(Enum):
    """Validation status for changes."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


@dataclass
class ChangeSet:
    """Model for tracking individual file changes."""
    request_id: str
    file_path: str
    operation: ChangeOperation
    change_summary: str
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_content: Optional[str] = None
    new_content: Optional[str] = None
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate change set after initialization."""
        if self.operation == ChangeOperation.CREATE and self.new_content is None:
            raise ValueError("CREATE operation requires new_content")
        if self.operation == ChangeOperation.DELETE and self.original_content is None:
            raise ValueError("DELETE operation requires original_content")
        if self.operation == ChangeOperation.MODIFY and (self.original_content is None or self.new_content is None):
            raise ValueError("MODIFY operation requires both original_content and new_content")
    
    def mark_applied(self):
        """Mark change as applied."""
        self.applied_at = datetime.now()
    
    def set_validation_status(self, status: ValidationStatus, message: Optional[str] = None):
        """Set validation status with optional message."""
        self.validation_status = status
        self.validation_message = message
    
    def is_valid(self) -> bool:
        """Check if change is valid."""
        return self.validation_status == ValidationStatus.VALID
    
    def has_warning(self) -> bool:
        """Check if change has warnings."""
        return self.validation_status == ValidationStatus.WARNING
    
    def is_invalid(self) -> bool:
        """Check if change is invalid."""
        return self.validation_status == ValidationStatus.INVALID
    
    def is_applied(self) -> bool:
        """Check if change has been applied."""
        return self.applied_at is not None
    
    def get_content_diff_size(self) -> int:
        """Calculate the size difference between original and new content."""
        if self.operation == ChangeOperation.CREATE:
            return len(self.new_content or "")
        elif self.operation == ChangeOperation.DELETE:
            return -(len(self.original_content or ""))
        elif self.operation == ChangeOperation.MODIFY:
            original_size = len(self.original_content or "")
            new_size = len(self.new_content or "")
            return new_size - original_size
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert change set to dictionary."""
        data = asdict(self)
        data['operation'] = self.operation.value
        data['validation_status'] = self.validation_status.value
        data['created_at'] = self.created_at.isoformat()
        if self.applied_at:
            data['applied_at'] = self.applied_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeSet':
        """Create change set from dictionary."""
        # Convert datetime strings back to datetime objects
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('applied_at'), str):
            data['applied_at'] = datetime.fromisoformat(data['applied_at'])
        
        # Convert enum strings to enums
        if isinstance(data.get('operation'), str):
            data['operation'] = ChangeOperation(data['operation'])
        if isinstance(data.get('validation_status'), str):
            data['validation_status'] = ValidationStatus(data['validation_status'])
        
        return cls(**data)
    
    @classmethod
    def create_file_change(cls, request_id: str, file_path: str, content: str, summary: str) -> 'ChangeSet':
        """Create a new file change."""
        return cls(
            request_id=request_id,
            file_path=file_path,
            operation=ChangeOperation.CREATE,
            new_content=content,
            change_summary=summary
        )
    
    @classmethod
    def modify_file_change(cls, request_id: str, file_path: str, original_content: str, 
                          new_content: str, summary: str) -> 'ChangeSet':
        """Create a file modification change."""
        return cls(
            request_id=request_id,
            file_path=file_path,
            operation=ChangeOperation.MODIFY,
            original_content=original_content,
            new_content=new_content,
            change_summary=summary
        )
    
    @classmethod
    def delete_file_change(cls, request_id: str, file_path: str, original_content: str, 
                          summary: str) -> 'ChangeSet':
        """Create a file deletion change."""
        return cls(
            request_id=request_id,
            file_path=file_path,
            operation=ChangeOperation.DELETE,
            original_content=original_content,
            change_summary=summary
        )