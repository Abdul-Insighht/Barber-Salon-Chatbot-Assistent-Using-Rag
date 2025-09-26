# endpoints.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List, Any, Optional
import logging
import requests

load_dotenv(".env1")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment")

app = FastAPI(title="Barber Salon API", version="1.0.0")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# N8N Webhook URL
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
if not N8N_WEBHOOK_URL:
    raise RuntimeError("Missing N8N_WEBHOOK_URL in environment (.env1)")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("endpoints")


# Pydantic models for request/response
class BookingRequest(BaseModel):
    barber_id: int
    service: str
    appointment_time: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = ""

class BookingResponse(BaseModel):
    success: bool
    message: str
    booking_id: Optional[int] = None
    calendar_event_id: Optional[str] = None
    calendar_link: Optional[str] = None

class N8NWebhookPayload(BaseModel):
    event_type: str
    booking_details: dict
    calendar_event: dict


def _parse_ts_item(item: Any) -> str:
    """Parse timestamp item to readable string"""
    if not item:
        return ""
    try:
        s = str(item)
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt.strftime("%Y-%m-%d %I:%M %p")
    except Exception:
        return str(item)


def call_n8n_webhook(booking_data: dict) -> dict:
    """Call n8n webhook to create booking and Google Calendar event"""
    try:
        logger.info(f"Calling n8n webhook with booking data")
        
        # Prepare payload for n8n webhook
        webhook_payload = {
            "event_type": "booking_created",
            "booking_details": {
                "barber_id": booking_data["barber_id"],
                "barber_name": booking_data["barber_name"],
                "service": booking_data["service"],
                "appointment_time": booking_data["appointment_time"],
                "customer_name": booking_data["customer_name"],
                "customer_phone": booking_data["customer_phone"],
                "customer_email": booking_data.get("customer_email", ""),
                "status": "confirmed",
                "created_at": datetime.now().isoformat(),
                "salon_name": "AI Barber Salon",
                "notes": f"Booking for {booking_data['service']} with {booking_data['barber_name']}"
            },
            "calendar_event": {
                "summary": f"Barber Appointment - {booking_data['service']}",
                "description": f"Customer: {booking_data['customer_name']}\nPhone: {booking_data['customer_phone']}\nEmail: {booking_data['customer_email']}\nService: {booking_data['service']}\nBarber: {booking_data['barber_name']}\nSalon: AI Barber Salon",
                "start_time": booking_data["appointment_time"],
                "duration_minutes": 60,  # Default 1 hour appointment
                "attendees": [booking_data.get("customer_email", "")] if booking_data.get("customer_email") else [],
                "location": "AI Barber Salon"
            }
        }
        
        # Make the API call to n8n webhook
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=webhook_payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "BarberSalonAPI/1.0"
            },
            timeout=30
        )
        
        response.raise_for_status()
        
        # Parse response
        result = response.json() if response.content else {}
        logger.info(f"n8n webhook response: {result}")
        
        return {
            "success": True,
            "message": "Booking created and added to Google Calendar",
            "calendar_event_id": result.get("calendar_event_id"),
            "booking_id": result.get("booking_id"),
            "calendar_link": result.get("calendar_link")
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling n8n webhook: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to create calendar event: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error in n8n webhook call: {str(e)}")
        return {
            "success": False,
            "error": f"Booking system error: {str(e)}"
        }


@app.get("/")
async def root():
    return {"message": "Barber Salon API is running", "version": "1.0.0"}


@app.get("/barbers", response_model=List[dict])
async def get_all_barbers():
    """Get all barbers with formatted data"""
    try:
        res = supabase.table("Barber_bookings").select("*").execute()
        if res.error:
            logger.error("Supabase error: %s", res.error)
            raise HTTPException(status_code=500, detail=str(res.error))
        
        rows = res.data or []
        
        # Format and normalize data
        formatted_barbers = []
        for r in rows:
            # Find available slot key (case-insensitive)
            available_slots_raw = []
            for k in list(r.keys()):
                if "available" in k.lower() and "slot" in k.lower():
                    available_slots_raw = r.get(k) or []
                    break
            
            # Format the barber data
            formatted_barber = {
                "id": r.get("id"),
                "name": r.get("Barber", "").strip(),
                "services": r.get("Services", ""),
                "services_list": [s.strip() for s in str(r.get("Services", "")).split(",") if s.strip()],
                "available_slots_raw": available_slots_raw,
                "available_slots_formatted": [_parse_ts_item(x) for x in available_slots_raw],
                "total_slots": len(available_slots_raw)
            }
            formatted_barbers.append(formatted_barber)
        
        return formatted_barbers
        
    except Exception as e:
        logger.exception("Error fetching barbers")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/barbers/{barber_id}")
async def get_barber(barber_id: int):
    """Get specific barber by ID"""
    try:
        res = supabase.table("Barber_bookings").select("*").eq("id", barber_id).execute()
        
        if res.error or not res.data:
            logger.error("Supabase error: %s", res.error)
            raise HTTPException(status_code=404, detail="Barber not found")
        
        row = res.data[0]
        
        # Find and format available slots
        available_slots_raw = []
        for k in list(row.keys()):
            if "available" in k.lower() and "slot" in k.lower():
                available_slots_raw = row.get(k) or []
                break
        
        # Format the response
        formatted_barber = {
            "id": row.get("id"),
            "name": row.get("Barber", "").strip(),
            "services": row.get("Services", ""),
            "services_list": [s.strip() for s in str(row.get("Services", "")).split(",") if s.strip()],
            "available_slots_raw": available_slots_raw,
            "available_slots_formatted": [_parse_ts_item(x) for x in available_slots_raw],
            "total_slots": len(available_slots_raw)
        }
        
        return formatted_barber
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching barber")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/barbers/{barber_id}/availability")
async def get_availability(barber_id: int, date: str = None):
    """Get availability for specific barber, optionally filtered by date"""
    try:
        res = supabase.table("Barber_bookings").select("*").eq("id", barber_id).execute()
        
        if res.error or not res.data:
            raise HTTPException(status_code=404, detail="Barber not found")
        
        row = res.data[0]
        barber_name = row.get("Barber", "").strip()
        
        # Find available slots
        raw_slots = []
        for k in row.keys():
            if "available" in k.lower() and "slot" in k.lower():
                raw_slots = row.get(k) or []
                break
        
        # Filter and format slots
        filtered_slots = []
        for s in raw_slots:
            if date:
                # Filter by date YYYY-MM-DD
                try:
                    st = str(s).replace("Z", "+00:00")
                    dt = datetime.fromisoformat(st)
                    if dt.strftime("%Y-%m-%d") != date:
                        continue
                except Exception:
                    pass
            filtered_slots.append({
                "raw": s,
                "formatted": _parse_ts_item(s)
            })
        
        return {
            "barber_id": barber_id,
            "barber_name": barber_name,
            "date_filter": date,
            "available_slots": filtered_slots,
            "total_available": len(filtered_slots)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in availability")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bookings", response_model=BookingResponse)
async def create_booking(booking: BookingRequest):
    """Create a new booking and add to Google Calendar via n8n webhook"""
    try:
        # First, verify the barber exists and has the requested slot
        barber_res = supabase.table("Barber_bookings").select("*").eq("id", booking.barber_id).execute()
        
        if barber_res.error or not barber_res.data:
            raise HTTPException(status_code=404, detail="Barber not found")
        
        barber_data = barber_res.data[0]
        barber_name = barber_data.get("Barber", "").strip()
        
        # Get current available slots
        current_slots = []
        slot_key = None
        for k in barber_data.keys():
            if "available" in k.lower() and "slot" in k.lower():
                current_slots = barber_data.get(k) or []
                slot_key = k
                break
        
        # Check if the requested slot is available
        slot_found = False
        updated_slots = []
        
        for slot in current_slots:
            formatted_slot = _parse_ts_item(slot)
            if formatted_slot == booking.appointment_time:
                slot_found = True
                # Don't add this slot to updated_slots (remove it)
            else:
                updated_slots.append(slot)
        
        if not slot_found:
            raise HTTPException(status_code=400, detail="Requested time slot is not available")
        
        # Verify the service is offered by this barber
        services = str(barber_data.get("Services", ""))
        available_services = [s.strip() for s in services.split(",") if s.strip()]
        
        if booking.service not in available_services:
            raise HTTPException(
                status_code=400, 
                detail=f"Service '{booking.service}' is not offered by {barber_name}. Available services: {', '.join(available_services)}"
            )
        
        # Prepare booking data for n8n webhook
        booking_data = {
            "barber_id": booking.barber_id,
            "barber_name": barber_name,
            "service": booking.service,
            "appointment_time": booking.appointment_time,
            "customer_name": booking.customer_name,
            "customer_phone": booking.customer_phone,
            "customer_email": booking.customer_email,
            "status": "confirmed"
        }
        
        # Call n8n webhook to create booking and Google Calendar event
        webhook_result = call_n8n_webhook(booking_data)
        
        if not webhook_result["success"]:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to create calendar event: {webhook_result.get('error', 'Unknown error')}"
            )
        
        # Update the barber's available slots (remove the booked slot)
        if slot_key:
            update_res = supabase.table("Barber_bookings").update({
                slot_key: updated_slots
            }).eq("id", booking.barber_id).execute()
            
            if update_res.error:
                logger.error(f"Error updating slots: {update_res.error}")
                # Don't fail the booking completely, but log the error
        
        # TODO: In a real app, you'd also insert the booking into a separate bookings table:
        # booking_insert_data = {
        #     **booking_data,
        #     "calendar_event_id": webhook_result.get("calendar_event_id"),
        #     "created_at": datetime.now().isoformat()
        # }
        # booking_res = supabase.table("bookings").insert(booking_insert_data).execute()
        
        return BookingResponse(
            success=True,
            message=f"Appointment successfully booked with {barber_name} for {booking.service} at {booking.appointment_time} and added to Google Calendar",
            booking_id=webhook_result.get("booking_id"),
            calendar_event_id=webhook_result.get("calendar_event_id"),
            calendar_link=webhook_result.get("calendar_link")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating booking")
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {str(e)}")


@app.get("/bookings")
async def get_all_bookings():
    """Get all bookings - placeholder for future implementation"""
    return {
        "message": "Bookings endpoint not fully implemented yet",
        "note": "In a real app, this would return all bookings from a separate bookings table"
    }


@app.get("/services")
async def get_all_services():
    """Get all unique services offered across all barbers"""
    try:
        res = supabase.table("Barber_bookings").select("Services").execute()
        
        if res.error:
            raise HTTPException(status_code=500, detail=str(res.error))
        
        all_services = set()
        for row in res.data or []:
            services = str(row.get("Services", ""))
            for service in services.split(","):
                service = service.strip()
                if service:
                    all_services.add(service)
        
        return {
            "services": sorted(list(all_services)),
            "total": len(all_services)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching services")
        raise HTTPException(status_code=500, detail=str(e))


# Test n8n webhook endpoint
@app.post("/test-webhook")
async def test_n8n_webhook(test_data: dict = None):
    """Test the n8n webhook connection"""
    try:
        if not test_data:
            test_data = {
                "barber_id": 1,
                "barber_name": "Test Barber",
                "service": "Test Service",
                "appointment_time": "2024-01-01 10:00 AM",
                "customer_name": "Test Customer",
                "customer_phone": "1234567890",
                "customer_email": "test@example.com"
            }
        
        result = call_n8n_webhook(test_data)
        return result
        
    except Exception as e:
        logger.exception("Error testing webhook")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        test_res = supabase.table("Barber_bookings").select("id").limit(1).execute()
        db_status = "connected" if not test_res.error else "error"
        
        # Test n8n webhook (optional - comment out if causing issues)
        # webhook_status = "unknown"
        # try:
        #     webhook_test = requests.get(N8N_WEBHOOK_URL, timeout=5)
        #     webhook_status = "reachable" if webhook_test.status_code else "unreachable"
        # except:
        #     webhook_status = "unreachable"
        
        return {
            "status": "healthy",
            "database": db_status,
            "n8n_webhook_url": N8N_WEBHOOK_URL,
            # "webhook_status": webhook_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Run with: uvicorn endpoints:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)