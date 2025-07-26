// AI Agents Project - Main JavaScript
class AIAgentsApp {
    constructor() {
        this.systemStatus = 'offline';
        this.agents = {};
        this.currentRequest = null;
        this.progressSteps = ['Repository Analysis', 'Request Analysis', 'Code Planning', 'Implementation'];
        this.currentStep = 0;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.checkSystemStatus();
        this.loadAgentStatuses();
        this.setupProgressTracking();
        
        // Auto-refresh status every 30 seconds
        setInterval(() => {
            this.checkSystemStatus();
            this.loadAgentStatuses();
        }, 30000);
        
        console.log('AI Agents Project initialized');
    }
    
    bindEvents() {
        // Submit request button
        document.getElementById('submit-request').addEventListener('click', () => {
            this.submitRequest();
        });
        
        // Enter key in textarea
        document.getElementById('user-request').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.submitRequest();
            }
        });
        
        // Agent reset buttons
        document.querySelectorAll('.reset-agent').forEach(button => {
            button.addEventListener('click', (e) => {
                const agentCard = e.target.closest('.agent-card');
                const agentType = agentCard.dataset.agent;
                this.resetAgent(agentType);
            });
        });
        
        // Footer links
        document.getElementById('view-logs').addEventListener('click', (e) => {
            e.preventDefault();
            this.viewLogs();
        });
        
        document.getElementById('clear-session').addEventListener('click', (e) => {
            e.preventDefault();
            this.clearSession();
        });
        
        // Agent node clicks
        document.querySelectorAll('.agent-node').forEach(node => {
            node.addEventListener('click', () => {
                this.showAgentInfo(node.dataset.agent);
            });
        });
    }
    
    async checkSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (response.ok) {
                this.updateSystemStatus('online', data);
            } else {
                this.updateSystemStatus('offline');
            }
        } catch (error) {
            console.error('Error checking system status:', error);
            this.updateSystemStatus('offline');
        }
    }
    
    updateSystemStatus(status, data = null) {
        this.systemStatus = status;
        const statusDot = document.getElementById('system-status');
        
        statusDot.className = `status-dot ${status}`;
        
        if (data) {
            // Update configuration info
            document.getElementById('max-messages').textContent = data.system.max_messages;
            
            const openaiStatus = document.getElementById('openai-status');
            openaiStatus.textContent = data.openai.api_key_valid ? 'Connected' : 'Disconnected';
            openaiStatus.className = `status-text ${data.openai.api_key_valid ? 'connected' : 'disconnected'}`;
            
            const githubStatus = document.getElementById('github-status');
            githubStatus.textContent = data.github.token_configured ? 'Configured' : 'Not Configured';
            githubStatus.className = `status-text ${data.github.token_configured ? 'connected' : 'disconnected'}`;
        }
    }
    
    async loadAgentStatuses() {
        const agentTypes = ['project_manager', 'prompt_ask_engineer', 'prompt_code_engineer', 'code_agent', 'github_manager'];
        
        for (const agentType of agentTypes) {
            try {
                const response = await fetch(`/api/agents/${agentType}/status`);
                const data = await response.json();
                
                if (response.ok) {
                    this.updateAgentStatus(agentType, data);
                } else {
                    this.updateAgentStatus(agentType, null);
                }
            } catch (error) {
                console.error(`Error loading ${agentType} status:`, error);
                this.updateAgentStatus(agentType, null);
            }
        }
    }
    
    updateAgentStatus(agentType, data) {
        const agentCard = document.querySelector(`[data-agent="${agentType}"]`);
        if (!agentCard) return;
        
        const statusElement = agentCard.querySelector('.agent-status');
        const messageCountElement = agentCard.querySelector('[data-stat="message_count"]');
        const temperatureElement = agentCard.querySelector('[data-stat="temperature"]');
        
        if (data) {
            statusElement.textContent = 'Online';
            statusElement.className = 'agent-status online';
            messageCountElement.textContent = `${data.message_count}/${data.max_messages}`;
            temperatureElement.textContent = data.temperature;
            
            this.agents[agentType] = data;
        } else {
            statusElement.textContent = 'Offline';
            statusElement.className = 'agent-status offline';
            messageCountElement.textContent = '-';
            temperatureElement.textContent = '-';
        }
    }
    
    async submitRequest() {
        const userRequest = document.getElementById('user-request').value.trim();
        const repoUrl = document.getElementById('repo-url').value.trim();
        
        if (!userRequest) {
            this.showToast('Please enter a request', 'error');
            return;
        }
        
        if (this.systemStatus === 'offline') {
            this.showToast('System is offline. Please wait for connection.', 'error');
            return;
        }
        
        // Disable submit button and show progress
        const submitButton = document.getElementById('submit-request');
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        
        this.showProgressSection();
        this.startProgressAnimation();
        
        try {
            const response = await fetch('/api/process_request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    request: userRequest,
                    repo_url: repoUrl || undefined
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showResults(result);
                this.completeProgress();
                this.showToast('Request processed successfully!', 'success');
            } else {
                throw new Error(result.error || 'Request failed');
            }
            
        } catch (error) {
            console.error('Error processing request:', error);
            this.showToast(`Error: ${error.message}`, 'error');
            this.hideProgressSection();
        } finally {
            // Re-enable submit button
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fas fa-paper-plane"></i> Process Request';
        }
    }
    
    showProgressSection() {
        const progressSection = document.getElementById('progress-section');
        progressSection.style.display = 'block';
        progressSection.classList.add('fade-in');
        
        // Reset progress
        this.currentStep = 0;
        this.updateProgressStep();
    }
    
    hideProgressSection() {
        const progressSection = document.getElementById('progress-section');
        progressSection.style.display = 'none';
    }
    
    startProgressAnimation() {
        const progressFill = document.getElementById('progress-fill');
        const currentStatus = document.getElementById('current-status');
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 2;
            
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            
            progressFill.style.width = `${progress}%`;
            
            // Update step based on progress
            const stepIndex = Math.floor((progress / 100) * this.progressSteps.length);
            if (stepIndex !== this.currentStep && stepIndex < this.progressSteps.length) {
                this.currentStep = stepIndex;
                this.updateProgressStep();
            }
        }, 100);
        
        this.progressInterval = interval;
    }
    
    updateProgressStep() {
        const steps = document.querySelectorAll('.step');
        const currentStatus = document.getElementById('current-status');
        
        steps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            if (index < this.currentStep) {
                step.classList.add('completed');
            } else if (index === this.currentStep) {
                step.classList.add('active');
            }
        });
        
        if (this.currentStep < this.progressSteps.length) {
            currentStatus.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                <span>${this.progressSteps[this.currentStep]}...</span>
            `;
        }
    }
    
    completeProgress() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        const progressFill = document.getElementById('progress-fill');
        const currentStatus = document.getElementById('current-status');
        const steps = document.querySelectorAll('.step');
        
        progressFill.style.width = '100%';
        steps.forEach(step => {
            step.classList.remove('active');
            step.classList.add('completed');
        });
        
        currentStatus.innerHTML = `
            <i class="fas fa-check-circle" style="color: #48bb78;"></i>
            <span>Processing complete!</span>
        `;
    }
    
    showResults(result) {
        const resultsSection = document.getElementById('results-section');
        const resultsContainer = document.getElementById('results-container');
        
        let resultsHTML = '';
        
        // Status
        resultsHTML += `
            <div class="result-item">
                <div class="result-title">
                    <i class="fas fa-info-circle"></i> Status: ${result.status}
                </div>
                <div class="result-content">${result.message}</div>
            </div>
        `;
        
        // Changes made
        if (result.changes_made !== undefined) {
            resultsHTML += `
                <div class="result-item">
                    <div class="result-title">
                        <i class="fas fa-${result.changes_made ? 'check' : 'times'}-circle"></i> 
                        Changes Made: ${result.changes_made ? 'Yes' : 'No'}
                    </div>
                </div>
            `;
        }
        
        // Analysis
        if (result.analysis) {
            resultsHTML += `
                <div class="result-item">
                    <div class="result-title">
                        <i class="fas fa-search"></i> Analysis
                    </div>
                    <div class="result-content">${result.analysis.analysis || 'Analysis completed'}</div>
                </div>
            `;
        }
        
        // Code tasks
        if (result.code_tasks && result.code_tasks.code_tasks) {
            resultsHTML += `
                <div class="result-item">
                    <div class="result-title">
                        <i class="fas fa-tasks"></i> Code Tasks (${result.code_tasks.code_tasks.length})
                    </div>
                    <div class="result-content">
                        <ul style="margin-left: 20px;">
                            ${result.code_tasks.code_tasks.map(task => `
                                <li><strong>${task.title}:</strong> ${task.description}</li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
        
        // Files to change
        if (result.code_tasks && result.code_tasks.files_to_change && result.code_tasks.files_to_change.length > 0) {
            resultsHTML += `
                <div class="result-item">
                    <div class="result-title">
                        <i class="fas fa-file-code"></i> Files to Modify
                    </div>
                    <div class="result-content">
                        <ul style="margin-left: 20px;">
                            ${result.code_tasks.files_to_change.map(file => `<li><code>${file}</code></li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
        
        resultsContainer.innerHTML = resultsHTML;
        resultsSection.style.display = 'block';
        resultsSection.classList.add('slide-up');
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    async resetAgent(agentType) {
        try {
            const response = await fetch(`/api/agents/${agentType}/reset`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showToast(`${agentType} reset successfully`, 'success');
                this.loadAgentStatuses(); // Refresh status
            } else {
                throw new Error(result.error || 'Reset failed');
            }
        } catch (error) {
            console.error('Error resetting agent:', error);
            this.showToast(`Error resetting agent: ${error.message}`, 'error');
        }
    }
    
    async viewLogs() {
        try {
            const response = await fetch('/api/logs?lines=100');
            const data = await response.json();
            
            if (response.ok) {
                this.showLogsModal(data.logs);
            } else {
                throw new Error(data.error || 'Failed to load logs');
            }
        } catch (error) {
            console.error('Error loading logs:', error);
            this.showToast(`Error loading logs: ${error.message}`, 'error');
        }
    }
    
    showLogsModal(logs) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 800px; max-height: 600px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3><i class="fas fa-file-alt"></i> System Logs</h3>
                    <button class="btn btn-secondary btn-small" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i> Close
                    </button>
                </div>
                <div class="code-block" style="max-height: 400px; overflow-y: auto;">
                    ${logs.map(log => `<div>${this.escapeHtml(log)}</div>`).join('')}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    async clearSession() {
        if (!confirm('Are you sure you want to clear the current session? This will remove all request history.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/session/clear', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showToast('Session cleared successfully', 'success');
                // Clear form
                document.getElementById('user-request').value = '';
                // Hide results
                document.getElementById('results-section').style.display = 'none';
                document.getElementById('progress-section').style.display = 'none';
            } else {
                throw new Error(result.error || 'Clear session failed');
            }
        } catch (error) {
            console.error('Error clearing session:', error);
            this.showToast(`Error clearing session: ${error.message}`, 'error');
        }
    }
    
    showAgentInfo(agentType) {
        const agentData = this.agents[agentType];
        if (!agentData) {
            this.showToast('Agent information not available', 'warning');
            return;
        }
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3><i class="fas fa-robot"></i> ${agentType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
                    <button class="btn btn-secondary btn-small" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i> Close
                    </button>
                </div>
                <div class="agent-info">
                    <p><strong>Status:</strong> Online</p>
                    <p><strong>Messages:</strong> ${agentData.message_count}/${agentData.max_messages}</p>
                    <p><strong>Temperature:</strong> ${agentData.temperature}</p>
                    <p><strong>Model:</strong> ${agentData.model}</p>
                    <p><strong>Last Activity:</strong> ${agentData.last_activity ? new Date(agentData.last_activity).toLocaleString() : 'None'}</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    setupProgressTracking() {
        // Initialize progress tracking elements
        const progressSection = document.getElementById('progress-section');
        const resultsSection = document.getElementById('results-section');
        
        // Initially hide sections
        progressSection.style.display = 'none';
        resultsSection.style.display = 'none';
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Hide and remove toast
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
    
    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }
    
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiAgentsApp = new AIAgentsApp();
});