"""
Helper utilities for AI Trip Planner
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import locale
import math


def format_currency(amount: float, currency: str = "USD", locale_name: str = "en_US") -> str:
    """
    Format a number as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code
        locale_name: Locale name
        
    Returns:
        Formatted currency string
    """
    try:
        # Set locale for currency formatting
        locale.setlocale(locale.LC_ALL, locale_name)
        
        # Format as currency
        formatted = locale.currency(amount, grouping=True)
        
        return formatted
        
    except (locale.Error, ValueError):
        # Fallback formatting
        if currency == "USD":
            return f"${amount:,.2f}"
        elif currency == "EUR":
            return f"€{amount:,.2f}"
        elif currency == "GBP":
            return f"£{amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"


def format_duration(hours: float) -> str:
    """
    Format duration in hours to human-readable string.
    
    Args:
        hours: Duration in hours
        
    Returns:
        Formatted duration string
    """
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif hours < 24:
        whole_hours = int(hours)
        minutes = int((hours - whole_hours) * 60)
        
        if minutes == 0:
            return f"{whole_hours} hour{'s' if whole_hours != 1 else ''}"
        else:
            return f"{whole_hours}h {minutes}m"
    else:
        days = int(hours // 24)
        remaining_hours = hours % 24
        
        if remaining_hours < 1:
            return f"{days} day{'s' if days != 1 else ''}"
        else:
            return f"{days}d {int(remaining_hours)}h"


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone is valid
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits) <= 15


def format_phone(phone: str, format_type: str = "US") -> str:
    """
    Format phone number.
    
    Args:
        phone: Phone number to format
        format_type: Format type (US, International)
        
    Returns:
        Formatted phone number
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    if format_type == "US" and len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif format_type == "International" and len(digits) >= 10:
        return f"+{digits}"
    else:
        return phone


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


def format_coordinates(lat: float, lon: float, precision: int = 4) -> str:
    """
    Format coordinates as a string.
    
    Args:
        lat: Latitude
        lon: Longitude
        precision: Decimal precision
        
    Returns:
        Formatted coordinates string
    """
    return f"{lat:.{precision}f}, {lon:.{precision}f}"


def parse_coordinates(coord_string: str) -> Optional[tuple]:
    """
    Parse coordinates from string.
    
    Args:
        coord_string: Coordinates string (e.g., "40.7128, -74.0060")
        
    Returns:
        Tuple of (latitude, longitude) or None if invalid
    """
    try:
        # Remove whitespace and split by comma
        coords = coord_string.strip().split(',')
        
        if len(coords) != 2:
            return None
        
        lat = float(coords[0].strip())
        lon = float(coords[1].strip())
        
        # Validate ranges
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)
        
        return None
        
    except (ValueError, IndexError):
        return None


def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a random ID.
    
    Args:
        prefix: Optional prefix
        length: Length of random part
        
    Returns:
        Generated ID
    """
    import random
    import string
    
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    if prefix:
        return f"{prefix}_{random_part}"
    else:
        return random_part


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length
        
    Returns:
        List of keywords
    """
    # Convert to lowercase and split by non-alphanumeric characters
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter by length and remove duplicates
    keywords = list(set(word for word in words if len(word) >= min_length))
    
    return keywords


def calculate_rating_score(ratings: List[float]) -> Dict[str, float]:
    """
    Calculate rating statistics.
    
    Args:
        ratings: List of ratings
        
    Returns:
        Dictionary with rating statistics
    """
    if not ratings:
        return {"average": 0.0, "count": 0, "min": 0.0, "max": 0.0}
    
    return {
        "average": sum(ratings) / len(ratings),
        "count": len(ratings),
        "min": min(ratings),
        "max": max(ratings)
    }


def format_rating(rating: float, max_rating: float = 5.0) -> str:
    """
    Format rating as stars.
    
    Args:
        rating: Rating value
        max_rating: Maximum rating value
        
    Returns:
        Formatted rating string
    """
    if rating < 0 or rating > max_rating:
        return "Invalid rating"
    
    # Calculate number of full stars
    full_stars = int(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = int(max_rating) - full_stars - half_star
    
    stars = "★" * full_stars + "☆" * half_star + "☆" * empty_stars
    
    return f"{stars} ({rating:.1f}/{max_rating})"


def parse_date_range(date_string: str) -> Optional[tuple]:
    """
    Parse date range from string.
    
    Args:
        date_string: Date range string (e.g., "2024-01-15 to 2024-01-20")
        
    Returns:
        Tuple of (start_date, end_date) or None if invalid
    """
    try:
        # Split by common separators
        parts = re.split(r'\s+(?:to|until|through|-)\s+', date_string.strip())
        
        if len(parts) != 2:
            return None
        
        start_date = datetime.strptime(parts[0].strip(), "%Y-%m-%d").date()
        end_date = datetime.strptime(parts[1].strip(), "%Y-%m-%d").date()
        
        if start_date <= end_date:
            return (start_date, end_date)
        
        return None
        
    except ValueError:
        return None


def format_date_range(start_date: datetime, end_date: datetime) -> str:
    """
    Format date range as string.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Formatted date range string
    """
    if start_date.date() == end_date.date():
        return start_date.strftime("%B %d, %Y")
    elif start_date.year == end_date.year and start_date.month == end_date.month:
        return f"{start_date.strftime('%B %d')} - {end_date.strftime('%d, %Y')}"
    elif start_date.year == end_date.year:
        return f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
    else:
        return f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
