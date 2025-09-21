"""
Budget Agent

Specialized agent for budget management, cost optimization, and financial planning.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from ..base_agent import BaseAgent, AgentConfig, AgentRole, AgentCapabilities, AgentMessage


class BudgetAgent(BaseAgent):
    """
    Agent specialized in budget management and cost optimization.
    
    Capabilities:
    - Track and manage trip budgets
    - Find cost-saving opportunities
    - Optimize spending across categories
    - Monitor price changes
    - Suggest budget alternatives
    - Generate cost reports
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="Budget Manager",
                role=AgentRole.BUDGET,
                capabilities=AgentCapabilities(
                    can_budget=True,
                    can_monitor=True,
                    max_concurrent_tasks=3
                ),
                model="gpt-4",
                temperature=0.1
            )
        super().__init__(config)
        
        # Budget-specific attributes
        self.budget_tracker = {}
        self.price_history = {}
        self.cost_optimization_rules = {}
        self.budget_alerts = {}
        self.currency_rates = {}
    
    async def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Process budget-related requests."""
        try:
            self.status = AgentStatus.RUNNING
            
            if message.message_type == "create_budget":
                return await self._create_budget(message.content)
            elif message.message_type == "track_expense":
                return await self._track_expense(message.content)
            elif message.message_type == "optimize_costs":
                return await self._optimize_costs(message.content)
            elif message.message_type == "find_deals":
                return await self._find_deals(message.content)
            elif message.message_type == "budget_report":
                return await self._generate_budget_report(message.content)
            elif message.message_type == "price_alert":
                return await self._set_price_alert(message.content)
            else:
                return {"error": f"Unknown message type: {message.message_type}"}
                
        except Exception as e:
            await self.handle_error(e)
            return {"error": str(e)}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute budget-related tasks."""
        task_type = task.get("type")
        
        if task_type == "budget_analysis":
            return await self._analyze_budget(task)
        elif task_type == "cost_optimization":
            return await self._optimize_budget_costs(task)
        elif task_type == "price_monitoring":
            return await self._monitor_prices(task)
        elif task_type == "budget_forecasting":
            return await self._forecast_budget(task)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def _create_budget(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Create a budget for a trip."""
        trip_id = content.get("trip_id")
        total_budget = content.get("total_budget", 5000)
        currency = content.get("currency", "USD")
        categories = content.get("categories", self._get_default_categories())
        
        if not trip_id:
            return {"error": "Trip ID is required"}
        
        budget = {
            "trip_id": trip_id,
            "total_budget": total_budget,
            "currency": currency,
            "categories": categories,
            "allocated_amounts": {},
            "spent_amounts": {},
            "remaining_amounts": {},
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Allocate budget across categories
        budget["allocated_amounts"] = await self._allocate_budget(total_budget, categories)
        budget["remaining_amounts"] = budget["allocated_amounts"].copy()
        budget["spent_amounts"] = {cat: 0 for cat in categories}
        
        # Store budget
        self.budget_tracker[trip_id] = budget
        
        return {
            "success": True,
            "budget": budget,
            "message": f"Budget created for trip {trip_id}"
        }
    
    def _get_default_categories(self) -> List[str]:
        """Get default budget categories."""
        return [
            "accommodation",
            "transportation",
            "food",
            "activities",
            "shopping",
            "miscellaneous"
        ]
    
    async def _allocate_budget(self, total_budget: float, categories: List[str]) -> Dict[str, float]:
        """Allocate budget across categories based on typical travel spending patterns."""
        # Default allocation percentages
        allocation_percentages = {
            "accommodation": 0.35,
            "transportation": 0.25,
            "food": 0.20,
            "activities": 0.15,
            "shopping": 0.03,
            "miscellaneous": 0.02
        }
        
        allocated = {}
        remaining_budget = total_budget
        
        for i, category in enumerate(categories):
            if i == len(categories) - 1:
                # Last category gets remaining budget
                allocated[category] = remaining_budget
            else:
                percentage = allocation_percentages.get(category, 0.1)
                amount = total_budget * percentage
                allocated[category] = round(amount, 2)
                remaining_budget -= amount
        
        return allocated
    
    async def _track_expense(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Track an expense against the budget."""
        trip_id = content.get("trip_id")
        category = content.get("category")
        amount = content.get("amount", 0)
        description = content.get("description", "")
        currency = content.get("currency", "USD")
        
        if trip_id not in self.budget_tracker:
            return {"error": f"No budget found for trip {trip_id}"}
        
        budget = self.budget_tracker[trip_id]
        
        if category not in budget["categories"]:
            return {"error": f"Invalid category: {category}"}
        
        # Convert currency if needed
        if currency != budget["currency"]:
            amount = await self._convert_currency(amount, currency, budget["currency"])
        
        # Update spent amounts
        budget["spent_amounts"][category] += amount
        budget["remaining_amounts"][category] = budget["allocated_amounts"][category] - budget["spent_amounts"][category]
        budget["last_updated"] = datetime.now().isoformat()
        
        # Check for budget alerts
        await self._check_budget_alerts(trip_id, category, budget)
        
        # Add expense to history
        expense_record = {
            "category": category,
            "amount": amount,
            "description": description,
            "currency": budget["currency"],
            "timestamp": datetime.now().isoformat()
        }
        
        if "expense_history" not in budget:
            budget["expense_history"] = []
        budget["expense_history"].append(expense_record)
        
        return {
            "success": True,
            "expense": expense_record,
            "remaining_budget": budget["remaining_amounts"][category],
            "total_remaining": sum(budget["remaining_amounts"].values())
        }
    
    async def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert currency amount."""
        if from_currency == to_currency:
            return amount
        
        # Mock currency conversion - in reality would use external API
        await asyncio.sleep(0.1)
        
        # Mock exchange rates
        rates = {
            "USD": 1.0,
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.0,
            "CAD": 1.25
        }
        
        from_rate = rates.get(from_currency, 1.0)
        to_rate = rates.get(to_currency, 1.0)
        
        return round((amount / from_rate) * to_rate, 2)
    
    async def _check_budget_alerts(self, trip_id: str, category: str, budget: Dict[str, Any]) -> None:
        """Check if budget alerts should be triggered."""
        remaining = budget["remaining_amounts"][category]
        allocated = budget["allocated_amounts"][category]
        
        # Alert thresholds
        if remaining <= 0:
            await self._trigger_alert(trip_id, "budget_exceeded", {
                "category": category,
                "allocated": allocated,
                "spent": budget["spent_amounts"][category]
            })
        elif remaining <= allocated * 0.1:  # 10% remaining
            await self._trigger_alert(trip_id, "budget_low", {
                "category": category,
                "remaining": remaining,
                "percentage": (remaining / allocated) * 100
            })
    
    async def _trigger_alert(self, trip_id: str, alert_type: str, data: Dict[str, Any]) -> None:
        """Trigger a budget alert."""
        alert = {
            "trip_id": trip_id,
            "alert_type": alert_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        if trip_id not in self.budget_alerts:
            self.budget_alerts[trip_id] = []
        self.budget_alerts[trip_id].append(alert)
        
        # Update memory
        self.update_memory({
            "type": "budget_alert",
            "trip_id": trip_id,
            "alert_type": alert_type
        })
    
    async def _optimize_costs(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize costs for a trip."""
        trip_id = content.get("trip_id")
        optimization_goals = content.get("goals", ["reduce_costs", "maintain_quality"])
        
        if trip_id not in self.budget_tracker:
            return {"error": f"No budget found for trip {trip_id}"}
        
        budget = self.budget_tracker[trip_id]
        optimizations = []
        
        # Analyze each category for optimization opportunities
        for category in budget["categories"]:
            category_optimizations = await self._optimize_category(
                trip_id, category, budget, optimization_goals
            )
            optimizations.extend(category_optimizations)
        
        return {
            "success": True,
            "trip_id": trip_id,
            "optimizations": optimizations,
            "potential_savings": sum(opt.get("savings", 0) for opt in optimizations)
        }
    
    async def _optimize_category(self, trip_id: str, category: str, budget: Dict[str, Any], 
                               goals: List[str]) -> List[Dict[str, Any]]:
        """Optimize costs for a specific category."""
        optimizations = []
        
        if category == "accommodation":
            optimizations.extend(await self._optimize_accommodation(trip_id, budget))
        elif category == "transportation":
            optimizations.extend(await self._optimize_transportation(trip_id, budget))
        elif category == "food":
            optimizations.extend(await self._optimize_food(trip_id, budget))
        elif category == "activities":
            optimizations.extend(await self._optimize_activities(trip_id, budget))
        
        return optimizations
    
    async def _optimize_accommodation(self, trip_id: str, budget: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find accommodation optimization opportunities."""
        await asyncio.sleep(0.1)
        
        return [
            {
                "category": "accommodation",
                "type": "alternative_accommodation",
                "description": "Consider hostels or vacation rentals for 30% savings",
                "savings": budget["allocated_amounts"]["accommodation"] * 0.3,
                "impact": "medium"
            },
            {
                "category": "accommodation",
                "type": "location_optimization",
                "description": "Stay slightly outside city center for 20% savings",
                "savings": budget["allocated_amounts"]["accommodation"] * 0.2,
                "impact": "low"
            }
        ]
    
    async def _optimize_transportation(self, trip_id: str, budget: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find transportation optimization opportunities."""
        await asyncio.sleep(0.1)
        
        return [
            {
                "category": "transportation",
                "type": "public_transport",
                "description": "Use public transportation instead of taxis",
                "savings": budget["allocated_amounts"]["transportation"] * 0.4,
                "impact": "medium"
            },
            {
                "category": "transportation",
                "type": "walking",
                "description": "Walk for short distances to save on transport",
                "savings": budget["allocated_amounts"]["transportation"] * 0.1,
                "impact": "low"
            }
        ]
    
    async def _optimize_food(self, trip_id: str, budget: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find food optimization opportunities."""
        await asyncio.sleep(0.1)
        
        return [
            {
                "category": "food",
                "type": "local_eateries",
                "description": "Eat at local restaurants instead of tourist spots",
                "savings": budget["allocated_amounts"]["food"] * 0.25,
                "impact": "high"
            },
            {
                "category": "food",
                "type": "cooking",
                "description": "Prepare some meals if accommodation allows",
                "savings": budget["allocated_amounts"]["food"] * 0.15,
                "impact": "medium"
            }
        ]
    
    async def _optimize_activities(self, trip_id: str, budget: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find activity optimization opportunities."""
        await asyncio.sleep(0.1)
        
        return [
            {
                "category": "activities",
                "type": "free_activities",
                "description": "Include more free activities like walking tours",
                "savings": budget["allocated_amounts"]["activities"] * 0.2,
                "impact": "low"
            },
            {
                "category": "activities",
                "type": "group_discounts",
                "description": "Look for group discounts on activities",
                "savings": budget["allocated_amounts"]["activities"] * 0.1,
                "impact": "medium"
            }
        ]
    
    async def _find_deals(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Find deals and discounts for trip components."""
        trip_id = content.get("trip_id")
        category = content.get("category", "all")
        
        if trip_id not in self.budget_tracker:
            return {"error": f"No budget found for trip {trip_id}"}
        
        deals = await self._search_deals(trip_id, category)
        
        return {
            "success": True,
            "trip_id": trip_id,
            "deals": deals
        }
    
    async def _search_deals(self, trip_id: str, category: str) -> List[Dict[str, Any]]:
        """Search for deals and discounts."""
        await asyncio.sleep(0.2)
        
        # Mock deals search
        all_deals = [
            {
                "category": "accommodation",
                "title": "Hotel Early Bird Discount",
                "discount": "15% off",
                "valid_until": "2024-02-28",
                "savings": 150,
                "description": "Book 30 days in advance for 15% discount"
            },
            {
                "category": "transportation",
                "title": "Flight Bundle Deal",
                "discount": "20% off",
                "valid_until": "2024-03-15",
                "savings": 200,
                "description": "Book flight + hotel together for 20% off"
            },
            {
                "category": "activities",
                "title": "Activity Pass",
                "discount": "25% off",
                "valid_until": "2024-04-01",
                "savings": 75,
                "description": "City pass for multiple attractions"
            }
        ]
        
        if category != "all":
            deals = [d for d in all_deals if d["category"] == category]
        else:
            deals = all_deals
        
        return deals
    
    async def _generate_budget_report(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive budget report."""
        trip_id = content.get("trip_id")
        
        if trip_id not in self.budget_tracker:
            return {"error": f"No budget found for trip {trip_id}"}
        
        budget = self.budget_tracker[trip_id]
        
        # Calculate summary statistics
        total_allocated = sum(budget["allocated_amounts"].values())
        total_spent = sum(budget["spent_amounts"].values())
        total_remaining = total_allocated - total_spent
        
        # Calculate category breakdown
        category_breakdown = []
        for category in budget["categories"]:
            allocated = budget["allocated_amounts"][category]
            spent = budget["spent_amounts"][category]
            remaining = allocated - spent
            percentage_spent = (spent / allocated * 100) if allocated > 0 else 0
            
            category_breakdown.append({
                "category": category,
                "allocated": allocated,
                "spent": spent,
                "remaining": remaining,
                "percentage_spent": round(percentage_spent, 1)
            })
        
        # Get recent expenses
        recent_expenses = budget.get("expense_history", [])[-10:]  # Last 10 expenses
        
        # Get alerts
        alerts = self.budget_alerts.get(trip_id, [])
        
        report = {
            "trip_id": trip_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_allocated": total_allocated,
                "total_spent": total_spent,
                "total_remaining": total_remaining,
                "percentage_spent": round((total_spent / total_allocated * 100), 1) if total_allocated > 0 else 0
            },
            "category_breakdown": category_breakdown,
            "recent_expenses": recent_expenses,
            "alerts": alerts,
            "currency": budget["currency"]
        }
        
        return {
            "success": True,
            "report": report
        }
    
    async def _set_price_alert(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Set up price alerts for specific items."""
        trip_id = content.get("trip_id")
        item_type = content.get("item_type")  # flight, hotel, activity
        target_price = content.get("target_price")
        current_price = content.get("current_price")
        
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Mock price alert setup
        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Price alert set for {item_type} at ${target_price}"
        }
    
    async def _analyze_budget(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze budget performance and trends."""
        trip_id = task.get("trip_id")
        
        if trip_id not in self.budget_tracker:
            return {"error": f"No budget found for trip {trip_id}"}
        
        budget = self.budget_tracker[trip_id]
        
        # Mock budget analysis
        return {
            "success": True,
            "analysis": {
                "budget_health": "good",
                "spending_trend": "on_track",
                "recommendations": ["Consider reducing activity budget", "Food spending is optimal"]
            }
        }
    
    async def _optimize_budget_costs(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize budget costs based on analysis."""
        return await self._optimize_costs(task)
    
    async def _monitor_prices(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor prices for budget items."""
        return {
            "success": True,
            "price_changes": [],
            "alerts_triggered": 0
        }
    
    async def _forecast_budget(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast budget needs based on current spending."""
        trip_id = task.get("trip_id")
        
        if trip_id not in self.budget_tracker:
            return {"error": f"No budget found for trip {trip_id}"}
        
        budget = self.budget_tracker[trip_id]
        
        # Mock budget forecasting
        return {
            "success": True,
            "forecast": {
                "projected_total_spend": sum(budget["allocated_amounts"].values()) * 0.9,
                "confidence": 0.85,
                "recommendations": ["Budget is on track", "Consider increasing activity budget"]
            }
        }
