"""
Booking Agent

Specialized agent for handling reservations, bookings, and external service integration.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from ..base_agent import BaseAgent, AgentConfig, AgentRole, AgentCapabilities, AgentMessage


class BookingAgent(BaseAgent):
    """
    Agent specialized in booking and reservation management.
    
    Capabilities:
    - Book flights, hotels, and activities
    - Manage reservations and cancellations
    - Handle payment processing
    - Coordinate with external booking APIs
    - Track booking status and confirmations
    - Handle booking modifications
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="Booking Manager",
                role=AgentRole.BOOKER,
                capabilities=AgentCapabilities(
                    can_book=True,
                    can_execute=True,
                    max_concurrent_tasks=5
                ),
                model="gpt-4",
                temperature=0.2
            )
        super().__init__(config)
        
        # Booking-specific attributes
        self.booking_systems = {}
        self.active_bookings = {}
        self.booking_history = []
        self.payment_methods = {}
        self.booking_templates = {}
        self.confirmation_tracker = {}
    
    async def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Process booking requests."""
        try:
            self.status = AgentStatus.RUNNING
            
            if message.message_type == "book_item":
                return await self._book_item(message.content)
            elif message.message_type == "cancel_booking":
                return await self._cancel_booking(message.content)
            elif message.message_type == "modify_booking":
                return await self._modify_booking(message.content)
            elif message.message_type == "check_booking_status":
                return await self._check_booking_status(message.content)
            elif message.message_type == "get_booking_details":
                return await self._get_booking_details(message.content)
            elif message.message_type == "process_payment":
                return await self._process_payment(message.content)
            else:
                return {"error": f"Unknown message type: {message.message_type}"}
                
        except Exception as e:
            await self.handle_error(e)
            return {"error": str(e)}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute booking tasks."""
        task_type = task.get("type")
        
        if task_type == "bulk_booking":
            return await self._bulk_booking(task)
        elif task_type == "booking_verification":
            return await self._verify_bookings(task)
        elif task_type == "payment_processing":
            return await self._process_payments(task)
        elif task_type == "booking_cleanup":
            return await self._cleanup_bookings(task)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def _book_item(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Book a specific item (flight, hotel, activity, etc.)."""
        item_type = content.get("item_type")
        booking_details = content.get("booking_details", {})
        trip_id = content.get("trip_id")
        payment_info = content.get("payment_info", {})
        
        if not item_type:
            return {"error": "Item type is required"}
        
        # Generate booking ID
        booking_id = f"{item_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create booking record
        booking = {
            "booking_id": booking_id,
            "trip_id": trip_id,
            "item_type": item_type,
            "booking_details": booking_details,
            "payment_info": payment_info,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "confirmation_code": None,
            "total_cost": 0,
            "currency": "USD"
        }
        
        # Process booking based on type
        if item_type == "flight":
            result = await self._book_flight(booking_details, payment_info)
        elif item_type == "hotel":
            result = await self._book_hotel(booking_details, payment_info)
        elif item_type == "activity":
            result = await self._book_activity(booking_details, payment_info)
        elif item_type == "restaurant":
            result = await self._book_restaurant(booking_details, payment_info)
        elif item_type == "transportation":
            result = await self._book_transportation(booking_details, payment_info)
        else:
            return {"error": f"Unsupported item type: {item_type}"}
        
        # Update booking with result
        if result.get("success"):
            booking.update({
                "status": "confirmed",
                "confirmation_code": result.get("confirmation_code"),
                "total_cost": result.get("total_cost", 0),
                "currency": result.get("currency", "USD"),
                "confirmed_at": datetime.now().isoformat()
            })
        else:
            booking.update({
                "status": "failed",
                "error": result.get("error"),
                "failed_at": datetime.now().isoformat()
            })
        
        # Store booking
        self.active_bookings[booking_id] = booking
        self.booking_history.append(booking)
        
        return {
            "success": result.get("success", False),
            "booking": booking,
            "message": result.get("message", "Booking processed")
        }
    
    async def _book_flight(self, details: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Book a flight."""
        # Mock flight booking process
        await asyncio.sleep(2)  # Simulate API call delay
        
        # Validate booking details
        required_fields = ["origin", "destination", "departure_date", "passengers"]
        for field in required_fields:
            if field not in details:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        # Mock successful booking
        return {
            "success": True,
            "confirmation_code": f"FL{datetime.now().strftime('%Y%m%d%H%M')}",
            "total_cost": details.get("price", 500),
            "currency": "USD",
            "message": "Flight booked successfully",
            "booking_reference": f"FL{datetime.now().strftime('%Y%m%d%H%M')}",
            "seat_assignment": "12A",
            "gate": "A15"
        }
    
    async def _book_hotel(self, details: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Book a hotel."""
        await asyncio.sleep(1.5)  # Simulate API call delay
        
        required_fields = ["hotel_id", "check_in", "check_out", "guests", "rooms"]
        for field in required_fields:
            if field not in details:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        return {
            "success": True,
            "confirmation_code": f"HT{datetime.now().strftime('%Y%m%d%H%M')}",
            "total_cost": details.get("price", 200),
            "currency": "USD",
            "message": "Hotel booked successfully",
            "booking_reference": f"HT{datetime.now().strftime('%Y%m%d%H%M')}",
            "room_number": "205",
            "check_in_time": "15:00"
        }
    
    async def _book_activity(self, details: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Book an activity or attraction."""
        await asyncio.sleep(1)  # Simulate API call delay
        
        required_fields = ["activity_id", "date", "participants", "time_slot"]
        for field in required_fields:
            if field not in details:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        return {
            "success": True,
            "confirmation_code": f"AC{datetime.now().strftime('%Y%m%d%H%M')}",
            "total_cost": details.get("price", 75),
            "currency": "USD",
            "message": "Activity booked successfully",
            "booking_reference": f"AC{datetime.now().strftime('%Y%m%d%H%M')}",
            "meeting_point": "Main entrance",
            "duration": "3 hours"
        }
    
    async def _book_restaurant(self, details: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Book a restaurant reservation."""
        await asyncio.sleep(0.5)  # Simulate API call delay
        
        required_fields = ["restaurant_id", "date", "time", "party_size"]
        for field in required_fields:
            if field not in details:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        return {
            "success": True,
            "confirmation_code": f"RS{datetime.now().strftime('%Y%m%d%H%M')}",
            "total_cost": 0,  # Usually no upfront cost for reservations
            "currency": "USD",
            "message": "Restaurant reservation confirmed",
            "booking_reference": f"RS{datetime.now().strftime('%Y%m%d%H%M')}",
            "table_number": "12",
            "special_requests": details.get("special_requests", "")
        }
    
    async def _book_transportation(self, details: Dict[str, Any], payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Book transportation (car rental, transfer, etc.)."""
        await asyncio.sleep(1.2)  # Simulate API call delay
        
        required_fields = ["service_type", "pickup_location", "pickup_date", "duration"]
        for field in required_fields:
            if field not in details:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        return {
            "success": True,
            "confirmation_code": f"TR{datetime.now().strftime('%Y%m%d%H%M')}",
            "total_cost": details.get("price", 150),
            "currency": "USD",
            "message": "Transportation booked successfully",
            "booking_reference": f"TR{datetime.now().strftime('%Y%m%d%H%M')}",
            "pickup_instructions": "Meet at terminal 2, gate A",
            "vehicle_details": "Toyota Camry - White"
        }
    
    async def _cancel_booking(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel an existing booking."""
        booking_id = content.get("booking_id")
        cancellation_reason = content.get("reason", "User requested")
        
        if booking_id not in self.active_bookings:
            return {"error": f"Booking {booking_id} not found"}
        
        booking = self.active_bookings[booking_id]
        
        # Check if cancellation is allowed
        if booking["status"] not in ["confirmed", "pending"]:
            return {"error": f"Cannot cancel booking in status: {booking['status']}"}
        
        # Process cancellation
        cancellation_result = await self._process_cancellation(booking, cancellation_reason)
        
        if cancellation_result.get("success"):
            booking["status"] = "cancelled"
            booking["cancelled_at"] = datetime.now().isoformat()
            booking["cancellation_reason"] = cancellation_reason
            booking["refund_amount"] = cancellation_result.get("refund_amount", 0)
            
            return {
                "success": True,
                "booking_id": booking_id,
                "refund_amount": cancellation_result.get("refund_amount", 0),
                "message": "Booking cancelled successfully"
            }
        else:
            return {
                "success": False,
                "error": cancellation_result.get("error", "Cancellation failed")
            }
    
    async def _process_cancellation(self, booking: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Process the actual cancellation with external systems."""
        # Mock cancellation process
        await asyncio.sleep(1)
        
        # Calculate refund based on cancellation policy
        total_cost = booking.get("total_cost", 0)
        item_type = booking.get("item_type")
        
        # Mock refund calculation
        if item_type == "flight":
            refund_amount = total_cost * 0.8  # 80% refund for flights
        elif item_type == "hotel":
            refund_amount = total_cost * 0.9  # 90% refund for hotels
        else:
            refund_amount = total_cost  # Full refund for activities
        
        return {
            "success": True,
            "refund_amount": refund_amount,
            "processing_time": "3-5 business days"
        }
    
    async def _modify_booking(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Modify an existing booking."""
        booking_id = content.get("booking_id")
        modifications = content.get("modifications", {})
        
        if booking_id not in self.active_bookings:
            return {"error": f"Booking {booking_id} not found"}
        
        booking = self.active_bookings[booking_id]
        
        if booking["status"] != "confirmed":
            return {"error": f"Cannot modify booking in status: {booking['status']}"}
        
        # Process modifications
        modification_result = await self._process_modifications(booking, modifications)
        
        if modification_result.get("success"):
            # Update booking details
            booking["booking_details"].update(modifications)
            booking["modified_at"] = datetime.now().isoformat()
            booking["modification_history"] = booking.get("modification_history", [])
            booking["modification_history"].append({
                "modifications": modifications,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "booking_id": booking_id,
                "modifications": modifications,
                "message": "Booking modified successfully"
            }
        else:
            return {
                "success": False,
                "error": modification_result.get("error", "Modification failed")
            }
    
    async def _process_modifications(self, booking: Dict[str, Any], modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Process booking modifications with external systems."""
        # Mock modification process
        await asyncio.sleep(1)
        
        # Check if modifications are allowed
        item_type = booking.get("item_type")
        allowed_modifications = {
            "flight": ["seat_assignment", "meal_preference"],
            "hotel": ["room_type", "special_requests"],
            "activity": ["time_slot", "participants"],
            "restaurant": ["time", "party_size", "special_requests"]
        }
        
        allowed = allowed_modifications.get(item_type, [])
        for key in modifications.keys():
            if key not in allowed:
                return {
                    "success": False,
                    "error": f"Modification '{key}' not allowed for {item_type}"
                }
        
        return {
            "success": True,
            "message": "Modifications processed successfully"
        }
    
    async def _check_booking_status(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Check the status of a booking."""
        booking_id = content.get("booking_id")
        
        if booking_id not in self.active_bookings:
            return {"error": f"Booking {booking_id} not found"}
        
        booking = self.active_bookings[booking_id]
        
        # Mock status check with external system
        await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "booking": booking,
            "external_status": "confirmed",  # Mock external status
            "last_checked": datetime.now().isoformat()
        }
    
    async def _get_booking_details(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a booking."""
        booking_id = content.get("booking_id")
        
        if booking_id not in self.active_bookings:
            return {"error": f"Booking {booking_id} not found"}
        
        booking = self.active_bookings[booking_id]
        
        return {
            "success": True,
            "booking": booking
        }
    
    async def _process_payment(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment for a booking."""
        booking_id = content.get("booking_id")
        payment_info = content.get("payment_info", {})
        
        if booking_id not in self.active_bookings:
            return {"error": f"Booking {booking_id} not found"}
        
        booking = self.active_bookings[booking_id]
        
        # Mock payment processing
        await asyncio.sleep(1)
        
        payment_result = await self._process_payment_with_provider(payment_info, booking)
        
        if payment_result.get("success"):
            booking["payment_status"] = "completed"
            booking["payment_id"] = payment_result.get("payment_id")
            booking["paid_at"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "payment_id": payment_result.get("payment_id"),
                "message": "Payment processed successfully"
            }
        else:
            return {
                "success": False,
                "error": payment_result.get("error", "Payment failed")
            }
    
    async def _process_payment_with_provider(self, payment_info: Dict[str, Any], booking: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment with external payment provider."""
        # Mock payment processing
        required_fields = ["card_number", "expiry_date", "cvv", "cardholder_name"]
        for field in required_fields:
            if field not in payment_info:
                return {"success": False, "error": f"Missing payment field: {field}"}
        
        # Mock successful payment
        return {
            "success": True,
            "payment_id": f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "transaction_id": f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "amount": booking.get("total_cost", 0),
            "currency": booking.get("currency", "USD")
        }
    
    async def _bulk_booking(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple bookings in bulk."""
        bookings = task.get("bookings", [])
        results = []
        
        for booking_request in bookings:
            result = await self._book_item(booking_request)
            results.append(result)
        
        return {
            "success": True,
            "results": results,
            "total_bookings": len(bookings),
            "successful_bookings": len([r for r in results if r.get("success")])
        }
    
    async def _verify_bookings(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Verify all bookings are still valid."""
        trip_id = task.get("trip_id")
        
        if not trip_id:
            return {"error": "Trip ID is required"}
        
        # Find bookings for this trip
        trip_bookings = [b for b in self.active_bookings.values() if b.get("trip_id") == trip_id]
        
        verification_results = []
        for booking in trip_bookings:
            result = await self._check_booking_status({"booking_id": booking["booking_id"]})
            verification_results.append(result)
        
        return {
            "success": True,
            "trip_id": trip_id,
            "verification_results": verification_results
        }
    
    async def _process_payments(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process payments for multiple bookings."""
        booking_ids = task.get("booking_ids", [])
        results = []
        
        for booking_id in booking_ids:
            result = await self._process_payment({
                "booking_id": booking_id,
                "payment_info": task.get("payment_info", {})
            })
            results.append(result)
        
        return {
            "success": True,
            "results": results
        }
    
    async def _cleanup_bookings(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up old or completed bookings."""
        # Move completed bookings older than 30 days to archive
        cutoff_date = datetime.now() - timedelta(days=30)
        
        cleaned_count = 0
        for booking_id, booking in list(self.active_bookings.items()):
            if (booking.get("status") in ["completed", "cancelled"] and 
                datetime.fromisoformat(booking.get("created_at", "")) < cutoff_date):
                del self.active_bookings[booking_id]
                cleaned_count += 1
        
        return {
            "success": True,
            "cleaned_bookings": cleaned_count,
            "remaining_active": len(self.active_bookings)
        }
    
    def get_booking_stats(self) -> Dict[str, Any]:
        """Get booking statistics."""
        total_bookings = len(self.booking_history)
        active_bookings = len(self.active_bookings)
        successful_bookings = len([b for b in self.booking_history if b.get("status") == "confirmed"])
        
        return {
            "total_bookings": total_bookings,
            "active_bookings": active_bookings,
            "successful_bookings": successful_bookings,
            "success_rate": successful_bookings / total_bookings if total_bookings > 0 else 0,
            "total_revenue": sum(b.get("total_cost", 0) for b in self.booking_history if b.get("status") == "confirmed")
        }
