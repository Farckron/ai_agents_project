from typing import Dict, Any, List
import json
from .base_agent import BaseAgent

class PromptAskEngineer(BaseAgent):
    def __init__(self):
        super().__init__("prompt_ask_engineer")
        self.log_message("Prompt Ask Engineer initialized")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze repository state and provide recommendations
        
        Input task structure:
        - request: user request
        - repo_context: current repository summary
        - action: type of analysis to perform
        """
        try:
            action = task.get('action', 'analyze_and_recommend')
            user_request = task.get('request', '')
            repo_context = task.get('repo_context', '')
            
            self.log_message(f"Processing action: {action}")
            
            if action == 'analyze_and_recommend':
                return self._analyze_and_recommend(user_request, repo_context)
            elif action == 'clarify_request':
                return self._clarify_request(user_request, repo_context)
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                }
                
        except Exception as e:
            error_msg = f"Error in Prompt Ask Engineer: {str(e)}"
            self.log_message(error_msg, "ERROR")
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def _analyze_and_recommend(self, user_request: str, repo_context: str) -> Dict[str, Any]:
        """Analyze user request against repository context and provide recommendations"""
        
        analysis_prompt = f"""
        As a Prompt Ask Engineer, analyze the following user request against the current repository state and provide recommendations.

        USER REQUEST: {user_request}

        CURRENT REPOSITORY STATE:
        {repo_context}

        Please provide:
        1. Analysis of what the user wants to achieve
        2. Assessment of current repository state
        3. Specific recommendations for implementation
        4. Potential challenges or considerations
        5. Whether changes are needed (true/false)
        6. Priority level (low/medium/high)

        Format your response as JSON with the following structure:
        {{
            "analysis": "detailed analysis of the request",
            "repository_assessment": "assessment of current state",
            "recommendations": ["list", "of", "specific", "recommendations"],
            "challenges": ["potential", "challenges"],
            "changes_needed": true/false,
            "priority": "low/medium/high",
            "estimated_complexity": "simple/moderate/complex"
        }}
        """
        
        response = self.call_openai(analysis_prompt)
        
        try:
            # Try to parse JSON response
            parsed_response = json.loads(response)
            
            return {
                'status': 'success',
                'analysis': parsed_response.get('analysis', ''),
                'repository_assessment': parsed_response.get('repository_assessment', ''),
                'recommendations': parsed_response.get('recommendations', []),
                'challenges': parsed_response.get('challenges', []),
                'changes_needed': parsed_response.get('changes_needed', False),
                'priority': parsed_response.get('priority', 'medium'),
                'estimated_complexity': parsed_response.get('estimated_complexity', 'moderate'),
                'raw_response': response
            }
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            self.log_message("Failed to parse JSON response, using text analysis", "WARNING")
            
            # Simple text analysis to determine if changes are needed
            changes_needed = any(keyword in response.lower() for keyword in [
                'fix', 'add', 'implement', 'create', 'modify', 'update', 'change'
            ])
            
            return {
                'status': 'success',
                'analysis': response,
                'repository_assessment': 'Analysis completed (text format)',
                'recommendations': [response],
                'challenges': [],
                'changes_needed': changes_needed,
                'priority': 'medium',
                'estimated_complexity': 'moderate',
                'raw_response': response
            }
    
    def _clarify_request(self, user_request: str, repo_context: str) -> Dict[str, Any]:
        """Clarify unclear user requests"""
        
        clarification_prompt = f"""
        As a Prompt Ask Engineer, the user has made a request that may need clarification.

        USER REQUEST: {user_request}

        REPOSITORY CONTEXT:
        {repo_context}

        Please:
        1. Identify any ambiguous aspects of the request
        2. Suggest specific questions to clarify the requirements
        3. Provide possible interpretations of the request
        4. Recommend the most likely intended action

        Respond in a conversational manner that helps clarify the user's intent.
        """
        
        response = self.call_openai(clarification_prompt)
        
        return {
            'status': 'success',
            'clarification_needed': True,
            'clarification_questions': response,
            'raw_response': response
        }
    
    def get_repository_summary(self, repo_data: Dict[str, Any]) -> str:
        """Generate a concise repository summary for analysis"""
        
        summary_prompt = f"""
        Create a short, focused summary of this repository for development planning:

        Repository Data:
        {json.dumps(repo_data, indent=2)}

        Focus on:
        - Main purpose and functionality
        - Key technologies and frameworks
        - Current development status
        - Recent changes or activity
        - Architecture overview

        Keep the summary concise but informative (max 200 words).
        """
        
        return self.call_openai(summary_prompt)
    
    def evaluate_task_priority(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate and prioritize a list of tasks"""
        
        prioritization_prompt = f"""
        As a Prompt Ask Engineer, evaluate and prioritize these tasks:

        TASKS:
        {json.dumps(tasks, indent=2)}

        For each task, assess:
        1. Impact on project goals
        2. Technical complexity
        3. Dependencies on other tasks
        4. User value
        5. Risk level

        Return the tasks in priority order with explanations.
        """
        
        response = self.call_openai(prioritization_prompt)
        
        # In a real implementation, would parse and return structured data
        return {
            'prioritized_tasks': response,
            'status': 'success'
        }