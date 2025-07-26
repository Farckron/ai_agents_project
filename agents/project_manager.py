from typing import Dict, Any, List
from .base_agent import BaseAgent
from .prompt_ask_engineer import PromptAskEngineer
from .prompt_code_engineer import PromptCodeEngineer
from .code_agent import CodeAgent
from .github_manager import GitHubManager
from .pr_manager import PRManager

class ProjectManager(BaseAgent):
    def __init__(self):
        super().__init__("project_manager")
        
        # Initialize other agents
        self.prompt_ask_engineer = PromptAskEngineer()
        self.prompt_code_engineer = PromptCodeEngineer()
        self.code_agent = CodeAgent()
        self.github_manager = GitHubManager()
        self.pr_manager = PRManager()
        
        # Task tracking
        self.current_tasks: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict[str, Any]] = []
        
        self.log_message("Project Manager initialized")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Main task processing logic following the canvas workflow"""
        try:
            task_type = task.get('type', 'general')
            user_request = task.get('request', '')
            
            self.log_message(f"Processing task: {task_type}")
            
            # Step 1: Get repository summary from GitHub Manager
            repo_context = self.github_manager.process_task({
                'action': 'get_repo_summary',
                'repo_url': task.get('repo_url', '')
            })
            
            # Step 2: Ask Prompt Ask Engineer for recommendations
            analysis_result = self.prompt_ask_engineer.process_task({
                'request': user_request,
                'repo_context': repo_context.get('summary', ''),
                'action': 'analyze_and_recommend'
            })
            
            # Step 3: Check if there are important changes needed
            if analysis_result.get('changes_needed', False):
                
                # Step 4: Get specific code tasks from Prompt Code Engineer
                code_tasks = self.prompt_code_engineer.process_task({
                    'user_request': user_request,
                    'analysis': analysis_result.get('analysis', ''),
                    'recommendations': analysis_result.get('recommendations', []),
                    'repo_context': repo_context.get('summary', '')
                })
                
                # Step 5: Ask for clearance to start work
                clearance_request = {
                    'files_to_change': code_tasks.get('files_to_change', []),
                    'proposed_changes': code_tasks.get('proposed_changes', []),
                    'estimated_impact': code_tasks.get('impact_analysis', '')
                }
                
                # For now, auto-approve (in real implementation, this would be user input)
                if self._request_clearance(clearance_request):
                    
                    # Step 6: Execute code changes
                    code_result = self.code_agent.process_task({
                        'tasks': code_tasks.get('code_tasks', []),
                        'files_to_change': code_tasks.get('files_to_change', []),
                        'context': repo_context.get('summary', '')
                    })
                    
                    return {
                        'status': 'completed',
                        'changes_made': True,
                        'analysis': analysis_result,
                        'code_tasks': code_tasks,
                        'code_result': code_result,
                        'message': 'Task completed successfully with code changes'
                    }
                else:
                    return {
                        'status': 'pending_approval',
                        'changes_made': False,
                        'clearance_request': clearance_request,
                        'message': 'Waiting for user approval to proceed with changes'
                    }
            
            else:
                return {
                    'status': 'completed',
                    'changes_made': False,
                    'analysis': analysis_result,
                    'message': 'No significant changes needed based on analysis'
                }
                
        except Exception as e:
            error_msg = f"Error in task processing: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return {
                'status': 'error',
                'error': error_msg,
                'message': 'Task processing failed'
            }
    
    def _request_clearance(self, clearance_request: Dict[str, Any]) -> bool:
        """Request user clearance for code changes"""
        self.log_message("Requesting clearance for code changes")
        
        # In a real implementation, this would prompt the user
        # For demo purposes, we'll auto-approve simple changes
        files_count = len(clearance_request.get('files_to_change', []))
        
        if files_count <= 3:  # Auto-approve simple changes
            self.log_message("Auto-approved: simple changes")
            return True
        else:
            self.log_message("Manual approval required: complex changes")
            return False  # Would require user input
    
    def coordinate_agents(self, task_distribution: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Coordinate tasks between multiple agents"""
        results = {}
        
        for agent_name, tasks in task_distribution.items():
            agent = getattr(self, agent_name, None)
            if agent:
                agent_results = []
                for task in tasks:
                    result = agent.process_task(task)
                    agent_results.append(result)
                results[agent_name] = agent_results
            else:
                self.log_message(f"Unknown agent: {agent_name}", "WARNING")
        
        return results
    
    def get_project_status(self) -> Dict[str, Any]:
        """Get overall project status"""
        return {
            'project_manager': self.get_status(),
            'agents': {
                'prompt_ask_engineer': self.prompt_ask_engineer.get_status(),
                'prompt_code_engineer': self.prompt_code_engineer.get_status(),
                'code_agent': self.code_agent.get_status(),
                'github_manager': self.github_manager.get_status(),
                'pr_manager': self.pr_manager.get_status()
            },
            'current_tasks': len(self.current_tasks),
            'completed_tasks': len(self.completed_tasks)
        }
    
    def handle_user_request(self, user_input: str, repo_url: str = None) -> Dict[str, Any]:
        """Main entry point for handling user requests"""
        task = {
            'type': 'user_request',
            'request': user_input,
            'repo_url': repo_url,
            'timestamp': self.message_history[-1]["timestamp"] if self.message_history else None
        }
        
        self.current_tasks.append(task)
        result = self.process_task(task)
        
        if result.get('status') == 'completed':
            self.completed_tasks.append({**task, 'result': result})
            self.current_tasks.remove(task)
        
        return result
    
    def handle_pr_request(self, user_input: str, repo_url: str, pr_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle requests specifically for creating Pull Requests"""
        try:
            self.log_message(f"Processing PR request for repo: {repo_url}")
            
            # Step 1: Initialize PR workflow
            pr_result = self.pr_manager.process_task({
                'action': 'process_pr_request',
                'user_request': user_input,
                'repo_url': repo_url,
                'options': pr_options or {}
            })
            
            if pr_result.get('status') != 'ready_for_changes':
                return pr_result
            
            # Step 2: Get repository context and analysis
            repo_context = pr_result.get('repo_analysis', {})
            
            # Step 3: Get recommendations from Prompt Ask Engineer
            analysis_result = self.prompt_ask_engineer.process_task({
                'request': user_input,
                'repo_context': repo_context.get('summary', ''),
                'action': 'analyze_and_recommend'
            })
            
            # Step 4: Generate code tasks
            code_tasks = self.prompt_code_engineer.process_task({
                'user_request': user_input,
                'analysis': analysis_result.get('analysis', ''),
                'recommendations': analysis_result.get('recommendations', []),
                'repo_context': repo_context.get('summary', '')
            })
            
            # Step 5: Execute code changes
            code_result = self.code_agent.process_task({
                'tasks': code_tasks.get('code_tasks', []),
                'files_to_change': code_tasks.get('files_to_change', []),
                'context': repo_context.get('summary', '')
            })
            
            # Step 6: Execute PR workflow with the generated changes
            final_result = self.pr_manager.execute_pr_workflow(
                workflow_id=pr_result['workflow_id'],
                changes=code_result
            )
            
            return {
                'status': final_result.get('status', 'completed'),
                'workflow_id': pr_result['workflow_id'],
                'pr_result': final_result,
                'analysis': analysis_result,
                'code_tasks': code_tasks,
                'code_result': code_result,
                'message': 'PR workflow completed successfully'
            }
            
        except Exception as e:
            error_msg = f"Error in PR request handling: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return {
                'status': 'error',
                'error': error_msg,
                'message': 'PR request processing failed'
            }