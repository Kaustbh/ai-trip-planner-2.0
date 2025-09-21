# AI Trip Planner - Multi-Agent System

An intelligent trip planning system powered by multiple AI agents working together to create personalized travel experiences.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized agents for planning, research, booking, and monitoring
- **Intelligent Planning**: AI-powered itinerary creation based on preferences and constraints
- **Real-time Data**: Live flight prices, hotel availability, weather forecasts
- **Personalization**: Learning from user preferences and past trips
- **Cost Optimization**: Finding the best deals across multiple providers
- **Risk Management**: Monitoring for changes and providing alternatives

## 🏗️ Architecture

### Agents
- **Planning Agent**: Creates initial trip structure and itinerary
- **Research Agent**: Gathers information about destinations, activities, and logistics
- **Booking Agent**: Handles reservations for flights, hotels, and activities
- **Monitoring Agent**: Tracks changes and provides updates
- **Budget Agent**: Manages costs and finds deals

### Key Components
- **Protocols**: MCP, A2A, and custom communication protocols
- **Tools**: External API integrations (Google, Booking.com, Weather APIs)
- **Memory**: Vector storage for trip data and user preferences
- **Workflows**: Orchestrated agent collaboration
- **Orchestrators**: LangGraph and CrewAI integration

## 🛠️ Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-trip-planner

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
python scripts/run_agent.py
```

## 📖 Usage

### Basic Trip Planning
```python
from orchestrators.trip_orchestrator import TripOrchestrator

orchestrator = TripOrchestrator()
trip = await orchestrator.plan_trip(
    destination="Tokyo, Japan",
    duration=7,
    budget=5000,
    preferences={
        "interests": ["culture", "food", "technology"],
        "accommodation": "hotel",
        "transportation": "flight"
    }
)
```

### CLI Interface
```bash
# Plan a new trip
python scripts/run_agent.py --destination "Paris" --duration 5 --budget 3000

# Monitor existing trip
python scripts/monitor_trip.py --trip-id "trip_123"

# Get recommendations
python scripts/get_recommendations.py --destination "Barcelona"
```

## 🔧 Configuration

Edit `configs/` files to customize:
- Model settings (`model_config.yaml`)
- API endpoints (`protocol_config.yaml`)
- Tool configurations (`tool_config.yaml`)

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test suites
pytest tests/test_agents.py
pytest tests/test_workflows.py
```

## 📊 Monitoring

The system includes comprehensive monitoring and telemetry:
- Agent performance metrics
- API usage tracking
- Cost monitoring
- User satisfaction scores

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details
