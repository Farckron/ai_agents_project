from typing import Dict, Any, List
import json
from .base_agent import BaseAgent

class PromptCodeEngineer(BaseAgent):
    def __init__(self):
        super().__init__("prompt_code_engineer")
        self.log_message("Prompt Code Engineer initialized")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create precise code tasks and prompts for the Code Agent
        
        Input task structure:
        - user_request: original user request
        - analysis: analysis from Prompt Ask Engineer
        - recommendations: list of recommendations
        - repo_context: repository context
        """
        try:
            user_request = task.get('user_request', '')
            analysis = task.get('analysis', '')
            recommendations = task.get('recommendations', [])
            repo_context = task.get('repo_context', '')
            
            self.log_message("Creating code tasks and prompts")
            
            # Generate specific code tasks
            code_tasks = self._generate_code_tasks(user_request, analysis, recommendations, repo_context)
            
            # Determine files that need to be changed
            files_to_change = self._identify_files_to_change(code_tasks, repo_context)
            
            # Create detailed prompts for each task
            detailed_prompts = self._create_detailed_prompts(code_tasks)
            
            # Analyze potential impact
            impact_analysis = self._analyze_impact(code_tasks, files_to_change)
            
            return {
                'status': 'success',
                'code_tasks': code_tasks,
                'files_to_change': files_to_change,
                'detailed_prompts': detailed_prompts,
                'impact_analysis': impact_analysis,
                'proposed_changes': self._summarize_proposed_changes(code_tasks)
            }
            
        except Exception as e:
            error_msg = f"Error in Prompt Code Engineer: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def _generate_code_tasks(self, user_request: str, analysis: str, recommendations: List[str], repo_context: str) -> List[Dict[str, Any]]:
        """Generate specific code tasks based on analysis and recommendations"""
        
        task_generation_prompt = f"""
        As a Prompt Code Engineer, create specific, actionable code tasks based on this analysis:

        USER REQUEST: {user_request}

        ANALYSIS: {analysis}

        RECOMMENDATIONS: {json.dumps(recommendations, indent=2)}

        REPOSITORY CONTEXT: {repo_context}

        Generate specific code tasks with the following structure for each task:
        {{
            "task_id": "unique_id",
            "title": "brief task title",
            "description": "detailed description of what needs to be done",
            "type": "create/modify/delete/refactor",
            "target_files": ["list", "of", "files"],
            "dependencies": ["list", "of", "dependent", "task_ids"],
            "estimated_effort": "low/medium/high",
            "technical_requirements": ["specific", "technical", "requirements"]
        }}

        Respond with a JSON array of tasks.
        """
        
        response = self.call_openai(task_generation_prompt)
        
        try:
            tasks = json.loads(response)
            if not isinstance(tasks, list):
                tasks = [tasks]
            
            # Add task IDs if missing
            for i, task in enumerate(tasks):
                if 'task_id' not in task:
                    task['task_id'] = f"task_{i+1}"
            
            return tasks
            
        except json.JSONDecodeError:
            # Fallback: create basic task structure
            self.log_message("Failed to parse task JSON, creating fallback tasks", "WARNING")
            return [{
                'task_id': 'task_1',
                'title': 'Implementation Task',
                'description': user_request,
                'type': 'modify',
                'target_files': [],
                'dependencies': [],
                'estimated_effort': 'medium',
                'technical_requirements': [user_request]
            }]
    
    def _identify_files_to_change(self, code_tasks: List[Dict[str, Any]], repo_context: str) -> List[str]:
        """Identify which files need to be modified"""
        
        file_identification_prompt = f"""
        Based on these code tasks and repository context, identify the specific files that need to be changed:

        CODE TASKS: {json.dumps(code_tasks, indent=2)}

        REPOSITORY CONTEXT: {repo_context}

        List the files that will need to be modified, created, or deleted. Be specific with file paths.
        Respond with a JSON array of file paths.
        """
        
        response = self.call_openai(file_identification_prompt)
        
        try:
            files = json.loads(response)
            return files if isinstance(files, list) else []
        except json.JSONDecodeError:
            # Extract file mentions from tasks
            files = []
            for task in code_tasks:
                files.extend(task.get('target_files', []))
            return list(set(files))
    
    def _create_detailed_prompts(self, code_tasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """Create detailed prompts for each code task"""
        
        detailed_prompts = {}
        
        for task in code_tasks:
            prompt_creation_request = f"""
            Create a detailed, specific prompt for the Code Agent to implement this task:

            TASK: {json.dumps(task, indent=2)}

            The prompt should include:
            1. Clear objective and requirements
            2. Specific implementation guidelines
            3. Code style and standards to follow
            4. Error handling requirements
            5. Testing considerations
            6. Integration points with existing code

            Make the prompt actionable and comprehensive.
            """
            
            detailed_prompt = self.call_openai(prompt_creation_request)
            detailed_prompts[task['task_id']] = detailed_prompt
        
        return detailed_prompts
    
    def _analyze_impact(self, code_tasks: List[Dict[str, Any]], files_to_change: List[str]) -> str:
        """Analyze the potential impact of the proposed changes"""
        
        impact_prompt = f"""
        Analyze the potential impact of these code changes:

        CODE TASKS: {json.dumps(code_tasks, indent=2)}

        FILES TO CHANGE: {json.dumps(files_to_change)}

        Consider:
        1. Risk level of changes
        2. Potential breaking changes
        3. Dependencies that might be affected
        4. Testing requirements
        5. Deployment considerations
        6. Performance implications

        Provide a comprehensive impact analysis.
        """
        
        return self.call_openai(impact_prompt)
    
    def _summarize_proposed_changes(self, code_tasks: List[Dict[str, Any]]) -> List[str]:
        """Create a summary of proposed changes for user review"""
        
        changes = []
        for task in code_tasks:
            change_summary = f"{task.get('type', 'modify').title()}: {task.get('title', 'Unnamed task')}"
            if task.get('target_files'):
                change_summary += f" (affects: {', '.join(task['target_files'])})"
            changes.append(change_summary)
        
        return changes
    
    def create_implementation_plan(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a detailed implementation plan with task ordering"""
        
        planning_prompt = f"""
        Create an implementation plan for these code tasks:

        TASKS: {json.dumps(tasks, indent=2)}

        Provide:
        1. Optimal task execution order considering dependencies
        2. Estimated timeline for each phase
        3. Risk mitigation strategies
        4. Rollback procedures if needed
        5. Testing strategy

        Format as a structured implementation plan.
        """
        
        plan = self.call_openai(planning_prompt)
        
        return {
            'implementation_plan': plan,
            'task_order': self._determine_task_order(tasks),
            'estimated_duration': self._estimate_duration(tasks)
        }
    
    def _determine_task_order(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Determine optimal task execution order"""
        # Simple dependency resolution
        ordered_tasks = []
        remaining_tasks = tasks.copy()
        
        while remaining_tasks:
            # Find tasks with no unresolved dependencies
            ready_tasks = []
            for task in remaining_tasks:
                dependencies = task.get('dependencies', [])
                if all(dep_id in [t['task_id'] for t in ordered_tasks] for dep_id in dependencies):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # No tasks ready - might be circular dependency, add remaining
                ready_tasks = remaining_tasks
            
            # Sort by effort (low effort first)
            effort_order = {'low': 1, 'medium': 2, 'high': 3}
            ready_tasks.sort(key=lambda t: effort_order.get(t.get('estimated_effort', 'medium'), 2))
            
            # Add first ready task to ordered list
            if ready_tasks:
                next_task = ready_tasks[0]
                ordered_tasks.append(next_task)
                remaining_tasks.remove(next_task)
        
        return [task['task_id'] for task in ordered_tasks]
    
    def _estimate_duration(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Estimate duration for tasks in hours"""
        effort_hours = {
            'low': 2,
            'medium': 6,
            'high': 16
        }
        
        total_hours = 0
        task_estimates = {}
        
        for task in tasks:
            effort = task.get('estimated_effort', 'medium')
            hours = effort_hours.get(effort, 6)
            task_estimates[task['task_id']] = hours
            total_hours += hours
        
        return {
            'total_hours': total_hours,
            'task_estimates': task_estimates,
            'estimated_days': max(1, total_hours // 8)
        }
    
    def validate_task_feasibility(self, task: Dict[str, Any], repo_context: str) -> Dict[str, Any]:
        """Validate if a task is feasible given the current repository state"""
        
        validation_prompt = f"""
        Validate the feasibility of this code task:

        TASK: {json.dumps(task, indent=2)}

        REPOSITORY CONTEXT: {repo_context}

        Check for:
        1. Technical feasibility
        2. Required dependencies availability
        3. Potential conflicts with existing code
        4. Resource requirements
        5. Complexity assessment

        Provide validation results with recommendations if changes are needed.
        """
        
        validation_result = self.call_openai(validation_prompt)
        
        return {
            'task_id': task.get('task_id'),
            'feasible': True,  # Would be determined from AI response
            'validation_notes': validation_result,
            'recommended_modifications': []
        }