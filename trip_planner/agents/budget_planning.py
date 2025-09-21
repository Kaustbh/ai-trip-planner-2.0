"""
Budget Planning Agent with LLM Integration
Estimates costs and creates intelligent budget breakdowns using AI-powered analysis.
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


class BudgetInput(BaseModel):
    """Input schema for budget planning."""
    destination: str = Field(description="Destination for budget estimation")
    duration_days: int = Field(description="Number of days for the trip")
    group_size: int = Field(default=1, description="Number of people traveling")
    budget: Optional[float] = Field(default=None, description="Total budget available")
    preferences: List[str] = Field(default_factory=list, description="User preferences affecting costs")


@tool(args_schema=BudgetInput)
def estimate_trip_budget(destination: str, duration_days: int, group_size: int = 1, 
                        budget: Optional[float] = None, preferences: List[str] = None) -> Dict[str, Any]:
    """
    Estimate budget breakdown for the trip.
    
    Args:
        destination: Destination for budget estimation
        duration_days: Number of days for the trip
        group_size: Number of people traveling
        preferences: User preferences affecting costs
    
    Returns:
        Budget breakdown with estimated costs
    """
    if preferences is None:
        preferences = []
    
    try:
        # Base daily costs per person (in USD) - these are rough estimates
        base_costs = {
            'accommodation': 80,  # Per night
            'food': 50,  # Per day
            'transportation': 30,  # Per day
            'activities': 40,  # Per day
            'miscellaneous': 20  # Per day
        }
        
        # Adjust costs based on destination (rough estimates)
        destination_multipliers = {
            'new york': 1.5,
            'london': 1.3,
            'paris': 1.2,
            'tokyo': 1.4,
            'singapore': 1.3,
            'dubai': 1.2,
            'mumbai': 0.3,
            'bangkok': 0.4,
            'prague': 0.6,
            'budapest': 0.5
        }
        
        # Get multiplier for destination
        multiplier = 1.0
        destination_lower = destination.lower()
        for dest, mult in destination_multipliers.items():
            if dest in destination_lower:
                multiplier = mult
                break
        
        # Adjust costs based on preferences
        if 'luxury' in [p.lower() for p in preferences]:
            multiplier *= 1.5
        elif 'budget' in [p.lower() for p in preferences]:
            multiplier *= 0.7
        
        # Calculate total costs
        total_daily_cost = sum(base_costs.values()) * multiplier
        total_cost = total_daily_cost * duration_days * group_size
        
        # Create detailed breakdown
        breakdown = {}
        for category, daily_cost in base_costs.items():
            category_total = daily_cost * multiplier * duration_days * group_size
            breakdown[category] = round(category_total, 2)
        
        # Add some additional categories
        breakdown['flights'] = round(500 * group_size * multiplier, 2)  # Rough flight estimate
        breakdown['travel_insurance'] = round(50 * group_size, 2)
        breakdown['visa_fees'] = round(100 * group_size, 2)
        
        # Calculate total
        total_estimated = sum(breakdown.values())
        
        # Add recommendations
        recommendations = []
        if budget and budget < total_estimated:
            recommendations.append(f"Budget of ${budget:,.2f} is below estimated cost of ${total_estimated:,.2f}")
            recommendations.append("Consider reducing trip duration or choosing budget accommodations")
        elif budget and budget > total_estimated * 1.2:
            recommendations.append(f"Budget of ${budget:,.2f} is well above estimated cost of ${total_estimated:,.2f}")
            recommendations.append("Consider upgrading accommodations or adding more activities")
        
        if 'luxury' in [p.lower() for p in preferences]:
            recommendations.append("Luxury preferences will increase costs significantly")
        
        return {
            'total_estimated': round(total_estimated, 2),
            'daily_average': round(total_estimated / duration_days, 2),
            'per_person': round(total_estimated / group_size, 2),
            'breakdown': breakdown,
            'recommendations': recommendations,
            'currency': 'USD'
        }
        
    except Exception as e:
        print(f"Error estimating budget: {str(e)}")
        return {
            'total_estimated': 0,
            'daily_average': 0,
            'per_person': 0,
            'breakdown': {},
            'recommendations': ['Error calculating budget'],
            'currency': 'USD'
        }


class BudgetAnalysisOutput(BaseModel):
    """Output schema for LLM budget analysis."""
    detailed_breakdown: Dict[str, float] = Field(description="Detailed cost breakdown")
    cost_explanations: Dict[str, str] = Field(description="Explanations for each cost category")
    money_saving_tips: List[str] = Field(description="Specific money-saving recommendations")
    budget_optimization: List[str] = Field(description="Budget optimization suggestions")
    cost_comparison: Dict[str, Any] = Field(description="Comparison with similar destinations")
    seasonal_factors: List[str] = Field(description="Seasonal cost variations")


class BudgetPlanningAgent:
    """Agent responsible for intelligent budget planning and cost estimation with LLM integration."""
    
    def __init__(self, llm):
        self.llm = llm
        self.tools = [estimate_trip_budget]
        
        # LLM prompts for different tasks
        self.budget_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel budget analyst and financial advisor specializing in travel costs.
            
            Analyze the trip budget and provide comprehensive financial insights:
            
            Destination: {destination}
            Duration: {duration_days} days
            Group size: {group_size} people
            Budget level: {budget_level}
            Preferences: {preferences}
            
            Base cost estimates: {base_costs}
            
            Provide detailed analysis including:
            1. Detailed cost breakdown with explanations for each category
            2. Destination-specific cost factors and variations
            3. Money-saving tips and budget optimization strategies
            4. Seasonal cost variations and timing recommendations
            5. Comparison with similar destinations
            6. Hidden costs and unexpected expenses to consider
            7. Value-for-money recommendations
            8. Budget allocation strategies for different preferences
            
            Make your analysis practical, actionable, and personalized to the user's needs."""),
            ("human", "Please provide a comprehensive budget analysis for this trip.")
        ])
        
        self.cost_optimization_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel cost optimization expert.
            
            Given the current budget breakdown and user preferences, provide specific recommendations to:
            1. Reduce costs without compromising experience quality
            2. Optimize spending allocation across categories
            3. Identify areas where spending more would add significant value
            4. Suggest alternative approaches to expensive activities
            5. Recommend timing strategies to reduce costs
            
            Current budget: {current_budget}
            User preferences: {preferences}
            Destination: {destination}
            Duration: {duration_days} days
            
            Provide specific, actionable recommendations."""),
            ("human", "How can this budget be optimized for maximum value?")
        ])
        
        # Output parser
        self.budget_parser = PydanticOutputParser(pydantic_object=BudgetAnalysisOutput)
    
    def plan_budget(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create intelligent budget breakdown using LLM analysis.
        
        Args:
            state: Current trip planning state
            
        Returns:
            Updated state with AI-enhanced budget information
        """
        try:
            destination = state.get('destination', '')
            duration_days = state.get('duration_days', 1)
            group_size = state.get('group_size', 1)
            budget = state.get('budget')
            preferences = state.get('preferences', [])
            
            if not destination:
                return {
                    **state,
                    'errors': state.get('errors', []) + ['No destination provided for budget planning'],
                    'current_step': 'error'
                }
            
            # Step 1: Get base budget estimates
            base_budget_data = estimate_trip_budget.invoke({
                'destination': destination,
                'duration_days': duration_days,
                'group_size': group_size,
                'budget': budget,
                'preferences': preferences
            })
            
            # Step 2: Use LLM to enhance budget analysis
            enhanced_budget = self._enhance_budget_with_llm(
                destination, duration_days, group_size, preferences, 
                budget, base_budget_data
            )
            
            # Step 3: Get cost optimization recommendations
            optimization_tips = self._get_cost_optimization_tips(
                destination, duration_days, preferences, enhanced_budget
            )
            
            # Combine base budget with LLM enhancements
            final_budget_data = {
                **base_budget_data,
                **enhanced_budget,
                'optimization_tips': optimization_tips
            }
            
            # Update state
            updated_state = {
                **state,
                'budget_breakdown': final_budget_data,
                'current_step': 'budget_planned',
                'messages': state.get('messages', []) + [
                    {
                        'type': 'info',
                        'content': f'Created AI-enhanced budget analysis: ${final_budget_data["total_estimated"]:,.2f} for {duration_days} days'
                    }
                ]
            }
            
            return updated_state
            
        except Exception as e:
            error_msg = f"Error planning budget: {str(e)}"
            return {
                **state,
                'errors': state.get('errors', []) + [error_msg],
                'current_step': 'error'
            }
    
    def _enhance_budget_with_llm(self, destination: str, duration_days: int, group_size: int, 
                                preferences: List[str], budget: Optional[float], 
                                base_costs: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to enhance budget analysis with intelligent insights."""
        try:
            # Determine budget level
            budget_level = "moderate"
            if budget:
                daily_budget_per_person = budget / (duration_days * group_size)
                if daily_budget_per_person < 50:
                    budget_level = "budget"
                elif daily_budget_per_person > 150:
                    budget_level = "luxury"
            
            # Get LLM response
            response = self.budget_analysis_prompt.invoke({
                'destination': destination,
                'duration_days': duration_days,
                'group_size': group_size,
                'budget_level': budget_level,
                'preferences': ', '.join(preferences) if preferences else 'general tourism',
                'base_costs': str(base_costs)
            })
            
            llm_response = self.llm.invoke(response)
            
            # Parse structured output
            try:
                parsed_output = self.budget_parser.parse(llm_response.content)
                return {
                    'detailed_breakdown': parsed_output.detailed_breakdown,
                    'cost_explanations': parsed_output.cost_explanations,
                    'money_saving_tips': parsed_output.money_saving_tips,
                    'budget_optimization': parsed_output.budget_optimization,
                    'cost_comparison': parsed_output.cost_comparison,
                    'seasonal_factors': parsed_output.seasonal_factors
                }
            except Exception as parse_error:
                print(f"Error parsing budget analysis: {parse_error}")
                # Fallback to basic enhancement
                return self._create_basic_budget_enhancement(base_costs, destination)
            
        except Exception as e:
            print(f"Error enhancing budget with LLM: {str(e)}")
            return self._create_basic_budget_enhancement(base_costs, destination)
    
    def _get_cost_optimization_tips(self, destination: str, duration_days: int, 
                                   preferences: List[str], budget_data: Dict[str, Any]) -> List[str]:
        """Get cost optimization recommendations from LLM."""
        try:
            response = self.cost_optimization_prompt.invoke({
                'current_budget': str(budget_data.get('breakdown', {})),
                'preferences': ', '.join(preferences) if preferences else 'general tourism',
                'destination': destination,
                'duration_days': duration_days
            })
            
            llm_response = self.llm.invoke(response)
            
            # Extract tips from response (simplified parsing)
            tips = []
            content = llm_response.content
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    tip = line.lstrip('-•* ').strip()
                    if tip:
                        tips.append(tip)
            
            return tips[:10]  # Limit to top 10 tips
            
        except Exception as e:
            print(f"Error getting optimization tips: {str(e)}")
            return ["Consider booking accommodations in advance for better rates"]
    
    def _create_basic_budget_enhancement(self, base_costs: Dict[str, Any], destination: str) -> Dict[str, Any]:
        """Create basic budget enhancement as fallback."""
        return {
            'detailed_breakdown': base_costs.get('breakdown', {}),
            'cost_explanations': {
                'accommodation': 'Hotel and lodging costs',
                'food': 'Meals and dining expenses',
                'transportation': 'Local transport and travel costs',
                'activities': 'Sightseeing and entertainment costs'
            },
            'money_saving_tips': [
                'Book accommodations in advance',
                'Look for free walking tours',
                'Eat at local restaurants',
                'Use public transportation'
            ],
            'budget_optimization': [
                'Consider staying in hostels or budget hotels',
                'Look for combo tickets for attractions',
                'Plan meals around happy hours'
            ],
            'cost_comparison': {},
            'seasonal_factors': ['Prices may vary by season']
        }
    
    def get_agent_tools(self):
        """Get tools available to this agent."""
        return self.tools
