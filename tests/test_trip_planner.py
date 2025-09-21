"""
Tests for the AI Trip Planner system.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
from trip_planner import TripPlanner
from trip_planner.state import Place, WeatherData, ItineraryDay


class TestTripPlanner:
    """Test cases for the TripPlanner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = TripPlanner(
            llm_provider="groq",
            llm_model="llama3-8b-8192"
        )
    
    def test_initialization(self):
        """Test TripPlanner initialization."""
        assert self.planner is not None
        assert self.planner.workflow is not None
    
    @patch('trip_planner.workflows.trip_planning_workflow.TripPlanningWorkflow.plan_trip')
    def test_plan_trip_basic(self, mock_plan_trip):
        """Test basic trip planning."""
        # Mock the workflow response
        mock_plan_trip.return_value = {
            'destination': 'New York City',
            'duration_days': 3,
            'places': [],
            'itinerary': [],
            'budget_breakdown': {'total_estimated': 1000},
            'current_step': 'completed'
        }
        
        result = self.planner.plan_trip(
            destination="New York City",
            duration_days=3
        )
        
        assert result['destination'] == 'New York City'
        assert result['duration_days'] == 3
        mock_plan_trip.assert_called_once()
    
    def test_plan_trip_validation(self):
        """Test trip planning input validation."""
        with pytest.raises(ValueError, match="Destination is required"):
            self.planner.plan_trip(destination="")
    
    def test_date_calculation(self):
        """Test automatic date calculation."""
        with patch.object(self.planner.workflow, 'plan_trip') as mock_plan:
            mock_plan.return_value = {'current_step': 'completed'}
            
            # Test with start and end dates
            result = self.planner.plan_trip(
                destination="Paris",
                start_date="2024-06-01",
                end_date="2024-06-05"
            )
            
            # Should calculate duration as 5 days
            call_args = mock_plan.call_args[1]
            assert call_args['duration_days'] == 5
    
    def test_default_values(self):
        """Test default value assignment."""
        with patch.object(self.planner.workflow, 'plan_trip') as mock_plan:
            mock_plan.return_value = {'current_step': 'completed'}
            
            result = self.planner.plan_trip(destination="Tokyo")
            
            call_args = mock_plan.call_args[1]
            assert call_args['duration_days'] == 3
            assert call_args['group_size'] == 1
            assert call_args['preferences'] == []


class TestPlaceModel:
    """Test cases for the Place model."""
    
    def test_place_creation(self):
        """Test Place model creation."""
        place = Place(
            name="Central Park",
            description="A large public park in Manhattan",
            rating=4.5,
            address="New York, NY",
            category="park"
        )
        
        assert place.name == "Central Park"
        assert place.description == "A large public park in Manhattan"
        assert place.rating == 4.5
        assert place.address == "New York, NY"
        assert place.category == "park"
    
    def test_place_optional_fields(self):
        """Test Place model with optional fields."""
        place = Place(name="Test Place")
        
        assert place.name == "Test Place"
        assert place.description == ""
        assert place.rating is None
        assert place.address is None
        assert place.category is None


class TestWeatherDataModel:
    """Test cases for the WeatherData model."""
    
    def test_weather_data_creation(self):
        """Test WeatherData model creation."""
        weather = WeatherData(
            date=date(2024, 6, 1),
            temperature_max=25.0,
            temperature_min=15.0,
            description="Sunny",
            humidity=60.0,
            wind_speed=10.0,
            precipitation=0.0
        )
        
        assert weather.date == date(2024, 6, 1)
        assert weather.temperature_max == 25.0
        assert weather.temperature_min == 15.0
        assert weather.description == "Sunny"
        assert weather.humidity == 60.0
        assert weather.wind_speed == 10.0
        assert weather.precipitation == 0.0


class TestItineraryDayModel:
    """Test cases for the ItineraryDay model."""
    
    def test_itinerary_day_creation(self):
        """Test ItineraryDay model creation."""
        place = Place(name="Test Place")
        weather = WeatherData(
            date=date(2024, 6, 1),
            temperature_max=25.0,
            temperature_min=15.0,
            description="Sunny"
        )
        
        itinerary_day = ItineraryDay(
            date=date(2024, 6, 1),
            places=[place],
            activities=["Visit Test Place"],
            weather=weather,
            notes="Test day"
        )
        
        assert itinerary_day.date == date(2024, 6, 1)
        assert len(itinerary_day.places) == 1
        assert itinerary_day.places[0].name == "Test Place"
        assert itinerary_day.activities == ["Visit Test Place"]
        assert itinerary_day.weather == weather
        assert itinerary_day.notes == "Test day"


@pytest.fixture
def sample_trip_plan():
    """Sample trip plan for testing."""
    return {
        'destination': 'New York City',
        'duration_days': 3,
        'group_size': 2,
        'budget': 2000,
        'preferences': ['museums', 'parks'],
        'places': [
            Place(name="Central Park", description="A large park"),
            Place(name="Met Museum", description="Art museum")
        ],
        'itinerary': [
            ItineraryDay(
                date=date(2024, 6, 1),
                places=[Place(name="Central Park")],
                activities=["Visit Central Park"]
            )
        ],
        'budget_breakdown': {
            'total_estimated': 2000,
            'daily_average': 666.67,
            'per_person': 1000
        },
        'weather_forecast': [
            WeatherData(
                date=date(2024, 6, 1),
                temperature_max=25.0,
                temperature_min=15.0,
                description="Sunny"
            )
        ],
        'recommendations': ["Book accommodations in advance"],
        'current_step': 'completed',
        'errors': [],
        'messages': []
    }


class TestTripSummary:
    """Test cases for trip summary printing."""
    
    def test_print_trip_summary(self, sample_trip_plan, capsys):
        """Test trip summary printing."""
        planner = TripPlanner()
        planner.print_trip_summary(sample_trip_plan)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "AI TRIP PLANNER - TRIP SUMMARY" in output
        assert "New York City" in output
        assert "3 days" in output
        assert "2 people" in output
        assert "Central Park" in output
        assert "Met Museum" in output
        assert "$2,000.00" in output


if __name__ == "__main__":
    pytest.main([__file__])
