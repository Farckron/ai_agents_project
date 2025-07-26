from typing import Dict, Any, List
import os
import json
from .base_agent import BaseAgent

class CodeAgent(BaseAgent):
    def __init__(self):
        super().__init__("code_agent")
        self.log_message("Code Agent initialized")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code tasks - writing, fixing, and editing code
        
        Input task structure:
        - tasks: list of code tasks to execute
        - files_to_change: list of files that need modification
        - context: repository context
        """
        try:
            tasks = task.get('tasks', [])
            files_to_change = task.get('files_to_change', [])
            context = task.get('context', '')
            
            self.log_message(f"Processing {len(tasks)} code tasks")
            
            results = []
            for code_task in tasks:
                task_result = self._execute_single_task(code_task, context)
                results.append(task_result)
                
                # Log task completion
                self.log_message(f"Completed task: {code_task.get('task_id', 'unknown')}")
            
            # Generate summary
            summary = self._generate_execution_summary(results)
            
            return {
                'status': 'success',
                'task_results': results,
                'files_modified': self._get_modified_files(results),
                'summary': summary,
                'total_tasks': len(tasks),
                'successful_tasks': len([r for r in results if r.get('status') == 'success'])
            }
            
        except Exception as e:
            error_msg = f"Error in Code Agent: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def _execute_single_task(self, task: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Execute a single code task"""
        
        task_id = task.get('task_id', 'unknown')
        task_type = task.get('type', 'modify')
        title = task.get('title', 'Untitled Task')
        description = task.get('description', '')
        target_files = task.get('target_files', [])
        
        self.log_message(f"Executing task {task_id}: {title}")
        
        try:
            if task_type == 'create':
                return self._create_new_code(task, context)
            elif task_type == 'modify':
                return self._modify_existing_code(task, context)
            elif task_type == 'delete':
                return self._delete_code(task, context)
            elif task_type == 'refactor':
                return self._refactor_code(task, context)
            else:
                return {
                    'task_id': task_id,
                    'status': 'error',
                    'message': f'Unknown task type: {task_type}'
                }
                
        except Exception as e:
            return {
                'task_id': task_id,
                'status': 'error',
                'message': f'Task execution failed: {str(e)}'
            }
    
    def _create_new_code(self, task: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Create new code files or functions"""
        
        creation_prompt = f"""
        As a Code Agent, create new code based on this task:

        TASK: {json.dumps(task, indent=2)}

        CONTEXT: {context}

        Requirements:
        1. Write clean, maintainable code
        2. Follow best practices and coding standards
        3. Include appropriate error handling
        4. Add meaningful comments and documentation
        5. Ensure code is testable

        For each target file, provide:
        - Complete file content
        - Explanation of the implementation
        - Any setup or configuration needed

        If creating multiple files, organize them logically.
        """
        
        code_response = self.call_openai(creation_prompt)
        
        return {
            'task_id': task.get('task_id'),
            'status': 'success',
            'action': 'create',
            'generated_code': code_response,
            'files_affected': task.get('target_files', []),
            'implementation_notes': 'New code created as specified'
        }
    
    def _modify_existing_code(self, task: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Modify existing code"""
        
        modification_prompt = f"""
        As a Code Agent, modify existing code based on this task:

        TASK: {json.dumps(task, indent=2)}

        CONTEXT: {context}

        For code modification:
        1. Identify the specific changes needed
        2. Preserve existing functionality unless explicitly changing it
        3. Maintain code style consistency
        4. Update related documentation/comments
        5. Consider backward compatibility

        Provide:
        - Specific changes to make to each file
        - Before/after code snippets where helpful
        - Explanation of modifications
        - Any side effects or considerations
        """
        
        modification_response = self.call_openai(modification_prompt)
        
        return {
            'task_id': task.get('task_id'),
            'status': 'success',
            'action': 'modify',
            'modifications': modification_response,
            'files_affected': task.get('target_files', []),
            'implementation_notes': 'Code modified as requested'
        }
    
    def _delete_code(self, task: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Delete code safely"""
        
        deletion_prompt = f"""
        As a Code Agent, plan safe deletion of code based on this task:

        TASK: {json.dumps(task, indent=2)}

        CONTEXT: {context}

        For safe code deletion:
        1. Identify dependencies that might be affected
        2. Check for references to code being deleted
        3. Plan cleanup of related imports/references
        4. Consider impact on tests
        5. Suggest migration steps if needed

        Provide:
        - List of code/files to delete
        - Dependencies to update
        - Cleanup steps required
        - Potential risks and mitigation
        """
        
        deletion_response = self.call_openai(deletion_prompt)
        
        return {
            'task_id': task.get('task_id'),
            'status': 'success',
            'action': 'delete',
            'deletion_plan': deletion_response,
            'files_affected': task.get('target_files', []),
            'implementation_notes': 'Deletion plan created - manual review recommended'
        }
    
    def _refactor_code(self, task: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Refactor existing code for better structure/performance"""
        
        refactoring_prompt = f"""
        As a Code Agent, refactor code based on this task:

        TASK: {json.dumps(task, indent=2)}

        CONTEXT: {context}

        For code refactoring:
        1. Improve code structure and readability
        2. Optimize performance where possible
        3. Reduce code duplication
        4. Improve maintainability
        5. Preserve existing functionality

        Provide:
        - Refactored code structure
        - Explanation of improvements made
        - Performance benefits expected
        - Migration guide if interfaces change
        """
        
        refactoring_response = self.call_openai(refactoring_prompt)
        
        return {
            'task_id': task.get('task_id'),
            'status': 'success',
            'action': 'refactor',
            'refactored_code': refactoring_response,
            'files_affected': task.get('target_files', []),
            'implementation_notes': 'Code refactored for improved structure'
        }
    
    def _generate_execution_summary(self, results: List[Dict[str, Any]]) -> str:
        """Generate a summary of all executed tasks"""
        
        successful_tasks = len([r for r in results if r.get('status') == 'success'])
        failed_tasks = len([r for r in results if r.get('status') == 'error'])
        
        summary_prompt = f"""
        Generate a concise summary of code execution results:

        RESULTS: {json.dumps(results, indent=2)}

        STATISTICS:
        - Total tasks: {len(results)}
        - Successful: {successful_tasks}
        - Failed: {failed_tasks}

        Provide:
        1. Overall execution status
        2. Key accomplishments
        3. Any issues encountered
        4. Recommendations for next steps
        """
        
        return self.call_openai(summary_prompt)
    
    def _get_modified_files(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract list of files that were modified"""
        modified_files = []
        for result in results:
            files_affected = result.get('files_affected', [])
            modified_files.extend(files_affected)
        
        return list(set(modified_files))  # Remove duplicates
    
    def generate_code_from_spec(self, specification: str, file_type: str = 'python') -> Dict[str, Any]:
        """Generate code from a detailed specification"""
        
        generation_prompt = f"""
        Generate {file_type} code based on this specification:

        SPECIFICATION:
        {specification}

        Requirements:
        1. Write production-ready code
        2. Include proper error handling
        3. Add comprehensive documentation
        4. Follow language-specific best practices
        5. Make code modular and testable

        Provide complete, working code with explanations.
        """
        
        generated_code = self.call_openai(generation_prompt)
        
        return {
            'status': 'success',
            'generated_code': generated_code,
            'file_type': file_type,
            'specification': specification
        }
    
    def review_code_quality(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Review code quality and suggest improvements"""
        
        review_prompt = f"""
        Review this {language} code for quality and suggest improvements:

        CODE:
        {code}

        Evaluate:
        1. Code structure and organization
        2. Error handling
        3. Performance considerations
        4. Security issues
        5. Best practices adherence
        6. Documentation quality

        Provide specific suggestions for improvement.
        """
        
        review_results = self.call_openai(review_prompt)
        
        return {
            'status': 'success',
            'review_results': review_results,
            'language': language,
            'code_length': len(code)
        }
    
    def fix_code_issues(self, code: str, issues: List[str], language: str = 'python') -> Dict[str, Any]:
        """Fix specific issues in code"""
        
        fix_prompt = f"""
        Fix these specific issues in the {language} code:

        CODE:
        {code}

        ISSUES TO FIX:
        {json.dumps(issues, indent=2)}

        Provide:
        1. Corrected code
        2. Explanation of fixes made
        3. Any additional improvements
        """
        
        fixed_code = self.call_openai(fix_prompt)
        
        return {
            'status': 'success',
            'fixed_code': fixed_code,
            'issues_addressed': issues,
            'language': language
        }