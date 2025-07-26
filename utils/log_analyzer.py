"""
Log analysis utilities for monitoring PR operations, performance, and security events
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import statistics


class LogAnalyzer:
    """
    Analyzer for structured logs to provide insights and monitoring data
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        
        # Log file mappings
        self.log_files = {
            'pr_operations': self.log_dir / 'pr_operations.log',
            'audit': self.log_dir / 'audit.log',
            'performance': self.log_dir / 'performance.log',
            'security': self.log_dir / 'security.log',
            'structured': self.log_dir / 'structured.log'
        }
    
    def _read_log_entries(self, log_file: Path, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Read and parse log entries from a file"""
        entries = []
        
        if not log_file.exists():
            return entries
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        
                        # Filter by timestamp if specified
                        if since:
                            entry_time = datetime.fromisoformat(entry.get('timestamp', ''))
                            if entry_time < since:
                                continue
                        
                        entries.append(entry)
                    except (json.JSONDecodeError, ValueError, KeyError):
                        # Skip malformed entries
                        continue
        
        except Exception as e:
            print(f"Error reading log file {log_file}: {e}")
        
        return entries
    
    def get_pr_operation_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of PR operations in the last N hours"""
        since = datetime.now() - timedelta(hours=hours)
        entries = self._read_log_entries(self.log_files['pr_operations'], since)
        
        summary = {
            'total_operations': len(entries),
            'operations_by_type': Counter(),
            'operations_by_status': Counter(),
            'workflows': defaultdict(list),
            'success_rate': 0.0,
            'average_duration': 0.0,
            'failed_operations': []
        }
        
        workflow_durations = []
        
        for entry in entries:
            operation = entry.get('operation', 'unknown')
            status = entry.get('status', 'unknown')
            workflow_id = entry.get('context', {}).get('workflow_id')
            
            summary['operations_by_type'][operation] += 1
            summary['operations_by_status'][status] += 1
            
            if workflow_id:
                summary['workflows'][workflow_id].append(entry)
            
            if status == 'failed':
                summary['failed_operations'].append({
                    'timestamp': entry.get('timestamp'),
                    'operation': operation,
                    'message': entry.get('message'),
                    'details': entry.get('details', {})
                })
            
            # Extract duration if available
            if 'duration_ms' in entry.get('details', {}):
                workflow_durations.append(entry['details']['duration_ms'])
        
        # Calculate success rate
        total_ops = summary['total_operations']
        if total_ops > 0:
            successful_ops = summary['operations_by_status'].get('success', 0)
            summary['success_rate'] = (successful_ops / total_ops) * 100
        
        # Calculate average duration
        if workflow_durations:
            summary['average_duration'] = statistics.mean(workflow_durations)
        
        return summary
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for the last N hours"""
        since = datetime.now() - timedelta(hours=hours)
        entries = self._read_log_entries(self.log_files['performance'], since)
        
        metrics = {
            'total_metrics': len(entries),
            'metrics_by_operation': defaultdict(list),
            'average_response_times': {},
            'slowest_operations': [],
            'performance_trends': []
        }
        
        for entry in entries:
            metric_name = entry.get('metric_name', 'unknown')
            value = entry.get('value', 0)
            operation = entry.get('operation', 'unknown')
            
            metrics['metrics_by_operation'][operation].append({
                'metric_name': metric_name,
                'value': value,
                'timestamp': entry.get('timestamp'),
                'unit': entry.get('unit', 'ms')
            })
        
        # Calculate averages and identify slow operations
        for operation, values in metrics['metrics_by_operation'].items():
            durations = [v['value'] for v in values if 'duration' in v['metric_name']]
            
            if durations:
                avg_duration = statistics.mean(durations)
                max_duration = max(durations)
                
                metrics['average_response_times'][operation] = {
                    'average_ms': avg_duration,
                    'max_ms': max_duration,
                    'count': len(durations)
                }
                
                # Identify slow operations (> 5 seconds)
                if max_duration > 5000:
                    metrics['slowest_operations'].append({
                        'operation': operation,
                        'max_duration_ms': max_duration,
                        'average_duration_ms': avg_duration,
                        'count': len(durations)
                    })
        
        # Sort slowest operations
        metrics['slowest_operations'].sort(key=lambda x: x['max_duration_ms'], reverse=True)
        
        return metrics
    
    def get_security_events(self, hours: int = 24) -> Dict[str, Any]:
        """Get security events for the last N hours"""
        since = datetime.now() - timedelta(hours=hours)
        entries = self._read_log_entries(self.log_files['security'], since)
        
        security_summary = {
            'total_events': len(entries),
            'events_by_type': Counter(),
            'events_by_severity': Counter(),
            'high_severity_events': [],
            'suspicious_ips': Counter(),
            'blocked_attempts': []
        }
        
        for entry in entries:
            event_type = entry.get('event_type', 'unknown')
            severity = entry.get('severity', 'medium')
            source_ip = entry.get('source_ip')
            
            security_summary['events_by_type'][event_type] += 1
            security_summary['events_by_severity'][severity] += 1
            
            if source_ip:
                security_summary['suspicious_ips'][source_ip] += 1
            
            if severity in ['high', 'critical']:
                security_summary['high_severity_events'].append({
                    'timestamp': entry.get('timestamp'),
                    'event_type': event_type,
                    'severity': severity,
                    'source_ip': source_ip,
                    'details': entry.get('details', {})
                })
            
            if 'blocked' in event_type or 'violation' in event_type:
                security_summary['blocked_attempts'].append({
                    'timestamp': entry.get('timestamp'),
                    'event_type': event_type,
                    'source_ip': source_ip,
                    'details': entry.get('details', {})
                })
        
        return security_summary
    
    def get_audit_trail(self, hours: int = 24, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get audit trail for the last N hours, optionally filtered by user"""
        since = datetime.now() - timedelta(hours=hours)
        entries = self._read_log_entries(self.log_files['audit'], since)
        
        if user_id:
            entries = [e for e in entries if e.get('user_id') == user_id]
        
        audit_summary = {
            'total_events': len(entries),
            'events_by_type': Counter(),
            'events_by_user': Counter(),
            'events_by_result': Counter(),
            'recent_events': [],
            'failed_actions': []
        }
        
        for entry in entries:
            event_type = entry.get('event_type', 'unknown')
            user = entry.get('user_id', 'anonymous')
            result = entry.get('result', 'unknown')
            
            audit_summary['events_by_type'][event_type] += 1
            audit_summary['events_by_user'][user] += 1
            audit_summary['events_by_result'][result] += 1
            
            # Keep recent events (last 50)
            if len(audit_summary['recent_events']) < 50:
                audit_summary['recent_events'].append({
                    'timestamp': entry.get('timestamp'),
                    'event_type': event_type,
                    'user_id': user,
                    'resource': entry.get('resource'),
                    'action': entry.get('action'),
                    'result': result
                })
            
            if result == 'failed':
                audit_summary['failed_actions'].append({
                    'timestamp': entry.get('timestamp'),
                    'event_type': event_type,
                    'user_id': user,
                    'resource': entry.get('resource'),
                    'action': entry.get('action'),
                    'details': entry.get('details', {})
                })
        
        # Sort recent events by timestamp (newest first)
        audit_summary['recent_events'].sort(
            key=lambda x: x['timestamp'], 
            reverse=True
        )
        
        return audit_summary
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health based on logs"""
        now = datetime.now()
        
        # Check last hour for critical issues
        pr_summary = self.get_pr_operation_summary(hours=1)
        performance = self.get_performance_metrics(hours=1)
        security = self.get_security_events(hours=1)
        
        health = {
            'overall_status': 'healthy',
            'timestamp': now.isoformat(),
            'issues': [],
            'warnings': [],
            'metrics': {
                'pr_success_rate': pr_summary['success_rate'],
                'average_response_time': performance.get('average_response_times', {}).get('create_pr', {}).get('average_ms', 0),
                'security_events': security['total_events'],
                'high_severity_security': len(security['high_severity_events'])
            }
        }
        
        # Check for issues
        if pr_summary['success_rate'] < 80:
            health['issues'].append(f"Low PR success rate: {pr_summary['success_rate']:.1f}%")
            health['overall_status'] = 'degraded'
        
        if len(security['high_severity_events']) > 0:
            health['issues'].append(f"{len(security['high_severity_events'])} high severity security events")
            health['overall_status'] = 'degraded'
        
        # Check for warnings
        slow_operations = [op for op in performance['slowest_operations'] if op['max_duration_ms'] > 10000]
        if slow_operations:
            health['warnings'].append(f"{len(slow_operations)} operations taking >10 seconds")
        
        if security['total_events'] > 50:  # More than 50 security events per hour
            health['warnings'].append(f"High security event volume: {security['total_events']} events/hour")
        
        # Set overall status
        if health['issues']:
            health['overall_status'] = 'unhealthy' if len(health['issues']) > 2 else 'degraded'
        elif health['warnings']:
            health['overall_status'] = 'warning'
        
        return health
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate a comprehensive daily report"""
        if date is None:
            date = datetime.now().date()
        
        # Get data for the entire day
        start_of_day = datetime.combine(date, datetime.min.time())
        hours_since_start = int((datetime.now() - start_of_day).total_seconds() / 3600)
        
        pr_summary = self.get_pr_operation_summary(hours=hours_since_start)
        performance = self.get_performance_metrics(hours=hours_since_start)
        security = self.get_security_events(hours=hours_since_start)
        audit = self.get_audit_trail(hours=hours_since_start)
        
        report = {
            'date': date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_pr_operations': pr_summary['total_operations'],
                'pr_success_rate': pr_summary['success_rate'],
                'total_security_events': security['total_events'],
                'total_audit_events': audit['total_events'],
                'average_response_time_ms': performance.get('average_response_times', {}).get('create_pr', {}).get('average_ms', 0)
            },
            'pr_operations': pr_summary,
            'performance': performance,
            'security': security,
            'audit': audit,
            'recommendations': []
        }
        
        # Generate recommendations
        if pr_summary['success_rate'] < 90:
            report['recommendations'].append("Investigate PR operation failures to improve success rate")
        
        if len(performance['slowest_operations']) > 0:
            report['recommendations'].append("Optimize slow operations to improve performance")
        
        if len(security['high_severity_events']) > 0:
            report['recommendations'].append("Review and address high severity security events")
        
        return report
    
    def export_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Export report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_report_{timestamp}.json"
        
        report_path = self.log_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return str(report_path)


# Convenience functions
def get_system_health() -> Dict[str, Any]:
    """Get current system health"""
    analyzer = LogAnalyzer()
    return analyzer.get_system_health()

def generate_daily_report() -> Dict[str, Any]:
    """Generate daily report for today"""
    analyzer = LogAnalyzer()
    return analyzer.generate_daily_report()

def get_pr_metrics(hours: int = 24) -> Dict[str, Any]:
    """Get PR operation metrics"""
    analyzer = LogAnalyzer()
    return analyzer.get_pr_operation_summary(hours)

def get_security_summary(hours: int = 24) -> Dict[str, Any]:
    """Get security events summary"""
    analyzer = LogAnalyzer()
    return analyzer.get_security_events(hours)