"""
Monitoring Agent

Responsible for monitoring trip progress, external changes, and system health.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import json

from .base_agent import BaseAgent, AgentConfig, AgentRole, AgentCapabilities, AgentMessage


class MonitoringAgent(BaseAgent):
    """
    Agent responsible for monitoring and alerting.
    
    Capabilities:
    - Monitor trip progress and changes
    - Track external service status
    - Send alerts and notifications
    - Monitor system health
    - Track performance metrics
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="System Monitor",
                role=AgentRole.MONITOR,
                capabilities=AgentCapabilities(
                    can_monitor=True,
                    can_learn=True,
                    max_concurrent_tasks=10
                ),
                model="gpt-4",
                temperature=0.1
            )
        super().__init__(config)
        
        # Monitoring-specific attributes
        self.monitored_trips = {}
        self.alert_rules = {}
        self.performance_metrics = {}
        self.health_checks = {}
        self.notification_handlers = {}
        self.monitoring_interval = 30  # seconds
        
    async def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Process monitoring requests."""
        try:
            self.status = AgentStatus.RUNNING
            
            if message.message_type == "start_monitoring":
                return await self._start_monitoring(message.content)
            elif message.message_type == "stop_monitoring":
                return await self._stop_monitoring(message.content)
            elif message.message_type == "add_alert_rule":
                return await self._add_alert_rule(message.content)
            elif message.message_type == "get_status":
                return await self._get_monitoring_status(message.content)
            elif message.message_type == "health_check":
                return await self._perform_health_check(message.content)
            else:
                return {"error": f"Unknown message type: {message.message_type}"}
                
        except Exception as e:
            await self.handle_error(e)
            return {"error": str(e)}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute monitoring tasks."""
        task_type = task.get("type")
        
        if task_type == "trip_monitoring":
            return await self._monitor_trip(task)
        elif task_type == "system_health":
            return await self._check_system_health(task)
        elif task_type == "performance_analysis":
            return await self._analyze_performance(task)
        elif task_type == "alert_processing":
            return await self._process_alerts(task)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def _start_monitoring(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Start monitoring a trip or system component."""
        trip_id = content.get("trip_id")
        monitoring_type = content.get("type", "trip")
        
        if monitoring_type == "trip":
            self.monitored_trips[trip_id] = {
                "trip_id": trip_id,
                "started_at": datetime.now(),
                "status": "active",
                "last_check": datetime.now(),
                "alerts": [],
                "metrics": {}
            }
            
            # Start background monitoring
            asyncio.create_task(self._monitor_trip_background(trip_id))
            
        return {
            "success": True,
            "trip_id": trip_id,
            "monitoring_type": monitoring_type,
            "message": "Monitoring started successfully"
        }
    
    async def _stop_monitoring(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Stop monitoring a trip or system component."""
        trip_id = content.get("trip_id")
        
        if trip_id in self.monitored_trips:
            self.monitored_trips[trip_id]["status"] = "stopped"
            self.monitored_trips[trip_id]["stopped_at"] = datetime.now()
            
            return {
                "success": True,
                "trip_id": trip_id,
                "message": "Monitoring stopped successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Trip {trip_id} not being monitored"
            }
    
    async def _add_alert_rule(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new alert rule."""
        rule_id = content.get("rule_id", f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        rule = content.get("rule", {})
        
        self.alert_rules[rule_id] = {
            "rule_id": rule_id,
            "rule": rule,
            "created_at": datetime.now(),
            "active": True,
            "trigger_count": 0
        }
        
        return {
            "success": True,
            "rule_id": rule_id,
            "message": "Alert rule added successfully"
        }
    
    async def _get_monitoring_status(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Get current monitoring status."""
        trip_id = content.get("trip_id")
        
        if trip_id:
            if trip_id in self.monitored_trips:
                return {
                    "success": True,
                    "trip_status": self.monitored_trips[trip_id]
                }
            else:
                return {
                    "success": False,
                    "error": f"Trip {trip_id} not being monitored"
                }
        else:
            return {
                "success": True,
                "monitored_trips": len(self.monitored_trips),
                "active_rules": len([r for r in self.alert_rules.values() if r["active"]]),
                "system_health": await self._get_system_health_summary()
            }
    
    async def _perform_health_check(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a health check on system components."""
        component = content.get("component", "all")
        
        health_results = {}
        
        if component == "all" or component == "agents":
            health_results["agents"] = await self._check_agent_health()
        
        if component == "all" or component == "external_apis":
            health_results["external_apis"] = await self._check_external_api_health()
        
        if component == "all" or component == "database":
            health_results["database"] = await self._check_database_health()
        
        return {
            "success": True,
            "health_check": health_results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _monitor_trip_background(self, trip_id: str) -> None:
        """Background task to monitor a trip."""
        while (trip_id in self.monitored_trips and 
               self.monitored_trips[trip_id]["status"] == "active"):
            
            try:
                # Perform monitoring checks
                await self._monitor_trip({"trip_id": trip_id})
                
                # Update last check time
                self.monitored_trips[trip_id]["last_check"] = datetime.now()
                
                # Wait for next check
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"Error monitoring trip {trip_id}: {str(e)}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _monitor_trip(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor a specific trip for changes and issues."""
        trip_id = task.get("trip_id")
        
        if trip_id not in self.monitored_trips:
            return {"error": f"Trip {trip_id} not being monitored"}
        
        trip_data = self.monitored_trips[trip_id]
        
        # Check for various issues
        issues = []
        
        # Check for flight changes
        flight_issues = await self._check_flight_changes(trip_id)
        if flight_issues:
            issues.extend(flight_issues)
        
        # Check for weather changes
        weather_issues = await self._check_weather_changes(trip_id)
        if weather_issues:
            issues.extend(weather_issues)
        
        # Check for booking confirmations
        booking_issues = await self._check_booking_status(trip_id)
        if booking_issues:
            issues.extend(booking_issues)
        
        # Process alerts
        for issue in issues:
            await self._process_alert(trip_id, issue)
        
        # Update metrics
        trip_data["metrics"]["last_check"] = datetime.now().isoformat()
        trip_data["metrics"]["issues_found"] = len(issues)
        
        return {
            "success": True,
            "trip_id": trip_id,
            "issues_found": len(issues),
            "issues": issues
        }
    
    async def _check_flight_changes(self, trip_id: str) -> List[Dict[str, Any]]:
        """Check for flight changes or delays."""
        # Mock flight monitoring
        issues = []
        
        # Simulate checking external API
        await asyncio.sleep(0.1)
        
        # Mock finding a delay
        if trip_id == "trip_123":  # Example trip
            issues.append({
                "type": "flight_delay",
                "severity": "medium",
                "message": "Flight ABC123 delayed by 2 hours",
                "affected_booking": "flight_booking_456",
                "timestamp": datetime.now().isoformat()
            })
        
        return issues
    
    async def _check_weather_changes(self, trip_id: str) -> List[Dict[str, Any]]:
        """Check for weather changes that might affect the trip."""
        issues = []
        
        # Mock weather monitoring
        await asyncio.sleep(0.1)
        
        # Mock finding severe weather
        if trip_id == "trip_456":  # Example trip
            issues.append({
                "type": "weather_warning",
                "severity": "high",
                "message": "Severe weather warning for destination",
                "affected_dates": ["2024-01-15", "2024-01-16"],
                "timestamp": datetime.now().isoformat()
            })
        
        return issues
    
    async def _check_booking_status(self, trip_id: str) -> List[Dict[str, Any]]:
        """Check booking status and confirmations."""
        issues = []
        
        # Mock booking status check
        await asyncio.sleep(0.1)
        
        # Mock finding a booking issue
        if trip_id == "trip_789":  # Example trip
            issues.append({
                "type": "booking_issue",
                "severity": "high",
                "message": "Hotel booking cancelled by provider",
                "affected_booking": "hotel_booking_789",
                "timestamp": datetime.now().isoformat()
            })
        
        return issues
    
    async def _process_alert(self, trip_id: str, issue: Dict[str, Any]) -> None:
        """Process an alert and take appropriate action."""
        # Add to trip's alert history
        if trip_id in self.monitored_trips:
            self.monitored_trips[trip_id]["alerts"].append(issue)
        
        # Check alert rules
        for rule_id, rule_data in self.alert_rules.items():
            if rule_data["active"] and self._should_trigger_alert(rule_data["rule"], issue):
                await self._trigger_alert(rule_id, trip_id, issue)
    
    def _should_trigger_alert(self, rule: Dict[str, Any], issue: Dict[str, Any]) -> bool:
        """Check if an issue should trigger an alert based on rules."""
        # Simple rule matching - in reality this would be more sophisticated
        if rule.get("type") == issue.get("type"):
            if rule.get("severity_threshold"):
                severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                issue_severity = severity_levels.get(issue.get("severity", "low"), 1)
                threshold = severity_levels.get(rule.get("severity_threshold"), 1)
                return issue_severity >= threshold
            return True
        return False
    
    async def _trigger_alert(self, rule_id: str, trip_id: str, issue: Dict[str, Any]) -> None:
        """Trigger an alert based on a rule."""
        rule = self.alert_rules[rule_id]
        rule["trigger_count"] += 1
        
        # Send notification
        notification = {
            "rule_id": rule_id,
            "trip_id": trip_id,
            "issue": issue,
            "timestamp": datetime.now().isoformat(),
            "action_taken": rule.get("action", "notify")
        }
        
        # In a real implementation, this would send actual notifications
        print(f"ALERT: {notification}")
        
        # Update memory
        self.update_memory({
            "type": "alert_triggered",
            "rule_id": rule_id,
            "trip_id": trip_id,
            "issue_type": issue.get("type")
        })
    
    async def _check_agent_health(self) -> Dict[str, Any]:
        """Check health of all agents in the system."""
        # Mock agent health check
        return {
            "status": "healthy",
            "active_agents": 5,
            "total_agents": 6,
            "last_check": datetime.now().isoformat()
        }
    
    async def _check_external_api_health(self) -> Dict[str, Any]:
        """Check health of external APIs."""
        # Mock API health check
        return {
            "status": "healthy",
            "apis_checked": ["google_maps", "amadeus", "booking"],
            "response_times": {
                "google_maps": 0.2,
                "amadeus": 0.5,
                "booking": 0.3
            },
            "last_check": datetime.now().isoformat()
        }
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        # Mock database health check
        return {
            "status": "healthy",
            "connection_pool": "active",
            "last_check": datetime.now().isoformat()
        }
    
    async def _get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        return {
            "overall_status": "healthy",
            "uptime": "99.9%",
            "last_incident": None,
            "active_monitors": len(self.monitored_trips)
        }
    
    async def _check_system_health(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check overall system health."""
        return await self._perform_health_check({"component": "all"})
    
    async def _analyze_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system performance metrics."""
        return {
            "success": True,
            "performance_metrics": {
                "average_response_time": 0.5,
                "throughput": 100,
                "error_rate": 0.01,
                "cpu_usage": 45.2,
                "memory_usage": 67.8
            }
        }
    
    async def _process_alerts(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process pending alerts."""
        return {
            "success": True,
            "alerts_processed": 0,
            "message": "No pending alerts"
        }
