# import os
# import logging
# from typing import List, Dict, Any, Optional
# from supabase import create_client, Client
# from dotenv import load_dotenv
# import google.generativeai as genai
# from datetime import datetime
# import json
# import re
# import requests

# # Load environment variables
# load_dotenv(".env1")

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("BarberChatbot")


# class BarberChatbot:
#     def __init__(self):
#         # Initialize Supabase
#         self.supabase_url = os.getenv("SUPABASE_URL")
#         self.supabase_key = os.getenv("SUPABASE_KEY")
        
#         if not self.supabase_url or not self.supabase_key:
#             raise ValueError("❌ SUPABASE_URL or SUPABASE_KEY is missing in .env")
        
#         self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
#         # Initialize Gemini AI
#         self.gemini_api_key = os.getenv("GEMINI_API_KEY")
#         if not self.gemini_api_key:
#             raise ValueError("❌ GEMINI_API_KEY is missing in .env")
        
#         genai.configure(api_key=self.gemini_api_key)
#         self.model = genai.GenerativeModel('gemini-2.0-flash')
        
#         # N8N Webhook URL from environment
#         self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
#         if not self.n8n_webhook_url:
#             raise ValueError("❌ N8N_WEBHOOK_URL is missing in .env1")
        
#         # Context for session
#         self.context = {
#             "booking_step": "initial",
#             "selected_barber": None,
#             "selected_barber_id": None,
#             "selected_service": None,
#             "selected_slot": None,
#             "customer_name": None,
#             "customer_phone": None,
#             "customer_email": None,
#             "booking_confirmed": False,
#             "booking_failed": False,
#             "calendar_event_id": None,
#             "conversation_history": []
#         }
        
#         # Cache for barber data
#         self.barbers_cache = None

#     # ---------- Database Methods ----------
#     def get_barbers_data(self) -> List[Dict[str, Any]]:
#         """Fetch all barbers from Supabase with caching"""
#         if self.barbers_cache is not None:
#             return self.barbers_cache
            
#         try:
#             logger.info("Fetching all barbers from Supabase")
#             response = self.client.table("Barber_bookings").select("*").execute()
#             data = response.data
#             logger.info(f"Raw Supabase response: {data}")

#             if not data:
#                 return []

#             # Normalize data
#             barbers = []
#             for row in data:
#                 barber_info = {
#                     "id": row.get("id"),
#                     "name": row.get("Barber", "").strip(),
#                     "services": row.get("Services", ""),
#                     "slots": row.get("Available Slots", [])
#                 }
#                 barbers.append(barber_info)
            
#             self.barbers_cache = barbers
#             return barbers
#         except Exception as e:
#             logger.error(f"Error fetching barbers: {str(e)}")
#             return []

#     def get_barber_by_id(self, barber_id: int) -> Optional[Dict[str, Any]]:
#         """Get specific barber by ID"""
#         barbers = self.get_barbers_data()
#         for barber in barbers:
#             if barber["id"] == barber_id:
#                 return barber
#         return None

#     def get_barber_by_name(self, barber_name: str) -> Optional[Dict[str, Any]]:
#         """Get specific barber by name"""
#         barbers = self.get_barbers_data()
#         barber_name_lower = barber_name.lower().strip()
#         for barber in barbers:
#             if barber["name"].lower() == barber_name_lower:
#                 return barber
#         return None

#     def get_available_slots(self, barber_id: int) -> List[str]:
#         """Fetch available slots for a specific barber"""
#         barber = self.get_barber_by_id(barber_id)
#         if not barber:
#             return []
        
#         slots = barber["slots"]  # Direct access instead of .get()
#         if isinstance(slots, list):
#             return [self.format_datetime(slot) for slot in slots]
#         return []

#     def get_barber_services(self, barber_id: int) -> List[str]:
#         """Get services offered by a specific barber"""
#         barber = self.get_barber_by_id(barber_id)
#         if not barber:
#             return []
        
#         services = barber["services"]  # Direct access instead of .get()
#         if isinstance(services, str):
#             return [service.strip() for service in services.split(",") if service.strip()]
#         return []

#     def format_datetime(self, datetime_str: str) -> str:
#         """Format datetime string to readable format"""
#         try:
#             dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
#             return dt.strftime("%Y-%m-%d %I:%M %p")
#         except:
#             return datetime_str

#     def call_n8n_webhook(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
#         """Call n8n webhook to create booking and Google Calendar event"""
#         try:
#             logger.info(f"Calling n8n webhook with data: {booking_data}")
            
#             # Prepare payload for n8n webhook
#             webhook_payload = {
#                 "event_type": "booking_created",
#                 "booking_details": {
#                     "barber_id": booking_data["barber_id"],
#                     "barber_name": booking_data["barber_name"],
#                     "service": booking_data["service"],
#                     "appointment_time": booking_data["appointment_time"],
#                     "customer_name": booking_data["customer_name"],
#                     "customer_phone": booking_data["customer_phone"],
#                     "customer_email": booking_data.get("customer_email", ""),
#                     "status": "confirmed",
#                     "created_at": datetime.now().isoformat(),
#                     "salon_name": "AI Barber Salon",
#                     "notes": f"Booking for {booking_data['service']} with {booking_data['barber_name']}"
#                 },
#                 "calendar_event": {
#                     "summary": f"Barber Appointment - {booking_data['service']}",
#                     "description": f"Customer: {booking_data['customer_name']}\nPhone: {booking_data['customer_phone']}\nEmail: {booking_data['customer_email']}\nService: {booking_data['service']}\nBarber: {booking_data['barber_name']}",
#                     "start_time": booking_data["appointment_time"],
#                     "duration_minutes": 60,  # Default 1 hour appointment
#                     "attendees": [booking_data.get("customer_email", "")]
#                 }
#             }
            
#             # Make the API call
#             response = requests.post(
#                 self.n8n_webhook_url,
#                 json=webhook_payload,
#                 headers={
#                     "Content-Type": "application/json",
#                     "User-Agent": "BarberSalonChatbot/1.0"
#                 },
#                 timeout=30
#             )
            
#             response.raise_for_status()
            
#             # Parse response - handle different response formats
#             result = {}
#             if response.content:
#                 try:
#                     raw_result = response.json()
#                     logger.info(f"n8n webhook response: {raw_result}")
                    
#                     # Handle different response formats from n8n
#                     if isinstance(raw_result, list):
#                         # If response is a list, extract data from first element
#                         if raw_result and isinstance(raw_result[0], dict):
#                             first_item = raw_result[0]
#                             # Check if it has content structure (like Gemini response)
#                             if "content" in first_item:
#                                 # Extract calendar link from the text content
#                                 text_content = ""
#                                 if "parts" in first_item["content"]:
#                                     for part in first_item["content"]["parts"]:
#                                         if "text" in part:
#                                             text_content += part["text"]
                                
#                                 # Extract calendar link from text
#                                 import re
#                                 calendar_link_match = re.search(r'https://www\.google\.com/calendar/event\?eid=[\w]+', text_content)
#                                 calendar_link = calendar_link_match.group(0) if calendar_link_match else None
                                
#                                 result = {
#                                     "calendar_link": calendar_link,
#                                     "calendar_event_id": "generated_by_n8n",
#                                     "booking_id": "n8n_booking",
#                                     "email_sent": True
#                                 }
#                             else:
#                                 result = first_item
#                     elif isinstance(raw_result, dict):
#                         result = raw_result
#                     else:
#                         result = {}
                        
#                 except json.JSONDecodeError:
#                     logger.warning("Could not parse n8n response as JSON")
#                     result = {}
            
#             return {
#                 "success": True,
#                 "message": "Booking created and added to Google Calendar",
#                 "calendar_event_id": result.get("calendar_event_id", "n8n_generated"),
#                 "booking_id": result.get("booking_id", "n8n_booking"),
#                 "calendar_link": result.get("calendar_link"),
#                 "email_sent": result.get("email_sent", False)
#             }
            
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Error calling n8n webhook: {str(e)}")
#             return {
#                 "success": False,
#                 "error": f"Failed to create calendar event: {str(e)}"
#             }
#         except Exception as e:
#             logger.error(f"Unexpected error in n8n webhook call: {str(e)}")
#             return {
#                 "success": False,
#                 "error": f"Booking system error: {str(e)}"
#             }

#     def book_appointment(self, barber_id: int, service: str, slot: str, customer_name: str, customer_phone: str, customer_email: str = "") -> Dict[str, Any]:
#         """Book appointment in the database and Google Calendar via n8n webhook"""
#         try:
#             barber = self.get_barber_by_id(barber_id)
#             if not barber:
#                 return {"success": False, "error": "Barber not found"}
            
#             # Prepare booking data
#             booking_data = {
#                 "barber_id": barber_id,
#                 "barber_name": barber["name"],  # Direct access instead of .get()
#                 "service": service,
#                 "appointment_time": slot,
#                 "customer_name": customer_name,
#                 "customer_phone": customer_phone,
#                 "customer_email": customer_email,
#                 "status": "confirmed",
#                 "created_at": datetime.now().isoformat()
#             }
            
#             # Call n8n webhook to create booking and calendar event
#             webhook_result = self.call_n8n_webhook(booking_data)
            
#             if not webhook_result["success"]:
#                 return webhook_result
            
#             # Update available slots in Supabase (remove booked slot)
#             current_slots = barber["slots"]  # Direct access instead of .get()
#             updated_slots = []
            
#             for existing_slot in current_slots:
#                 formatted_slot = self.format_datetime(existing_slot)
#                 if formatted_slot != slot:
#                     updated_slots.append(existing_slot)
            
#             # Update the barber's available slots in database
#             update_response = self.client.table("Barber_bookings").update({
#                 "Available Slots": updated_slots
#             }).eq("id", barber_id).execute()
            
#             if update_response.error:
#                 logger.error(f"Error updating available slots: {update_response.error}")
#                 # Don't fail the booking if slot update fails, but log it
            
#             # Clear cache to force refresh
#             self.barbers_cache = None
            
#             # Store calendar event ID in context
#             self.context["calendar_event_id"] = webhook_result.get("calendar_event_id")
            
#             return {
#                 "success": True,
#                 "message": "Appointment booked successfully and added to Google Calendar",
#                 "calendar_event_id": webhook_result.get("calendar_event_id"),
#                 "booking_id": webhook_result.get("booking_id"),
#                 "calendar_link": webhook_result.get("calendar_link")
#             }
            
#         except Exception as e:
#             logger.error(f"Error booking appointment: {str(e)}")
#             return {"success": False, "error": str(e)}

#     # ---------- RAG Knowledge Base ----------
#     def build_knowledge_base(self) -> str:
#         """Build knowledge base from barber data"""
#         barbers = self.get_barbers_data()
        
#         knowledge = "BARBER SALON INFORMATION:\n\n"
        
#         for barber in barbers:
#             knowledge += f"Barber ID: {barber['id']}\n"
#             knowledge += f"Barber Name: {barber['name']}\n"
            
#             # Services
#             services = self.get_barber_services(barber['id'])
#             knowledge += f"Services: {', '.join(services)}\n"
            
#             # Available slots
#             slots = self.get_available_slots(barber['id'])
#             knowledge += f"Available Slots: {', '.join(slots[:10])}{'...' if len(slots) > 10 else ''}\n"
#             knowledge += "---\n"
        
#         return knowledge

#     def create_dynamic_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
#         """Create dynamic prompt based on context and user input"""
        
#         knowledge_base = self.build_knowledge_base()
        
#         # Determine current booking step and create appropriate prompt
#         booking_step = context.get('booking_step', 'initial')
        
#         system_prompt = f"""
# You are a friendly and helpful AI barber salon assistant. Your job is to help customers find barbers, services, and book appointments efficiently.

# CURRENT SALON DATA:
# {knowledge_base}

# CURRENT BOOKING CONTEXT:
# - Booking Step: {booking_step}
# - Selected Barber: {context.get('selected_barber', 'None')} (ID: {context.get('selected_barber_id', 'None')})
# - Selected Service: {context.get('selected_service', 'None')}
# - Selected Slot: {context.get('selected_slot', 'None')}
# - Customer Name: {context.get('customer_name', 'None')}
# - Customer Phone: {context.get('customer_phone', 'None')}
# - Customer Email: {context.get('customer_email', 'None')}

# CRITICAL BOOKING FLOW RULES:
# 1. NEVER repeat information that has already been confirmed
# 2. NEVER ask for the same information twice
# 3. Move forward in the booking process, don't go backwards
# 4. When user provides all required info (barber, service, slot, name, phone, email), proceed to confirmation
# 5. DO NOT show available slots again if a slot has already been selected
# 6. Appointments will be automatically added to Google Calendar upon confirmation
# 7. ALWAYS ask for NAME, PHONE NUMBER, AND EMAIL ADDRESS together when collecting customer details - say "I'll need your full name, phone number, and email address"
# 8. EMAIL ADDRESS is REQUIRED - never proceed to booking without collecting the customer's email

# BOOKING PROCESS STEPS:
# 1. initial - User asking general questions or starting conversation
# 2. barber_selected - User has chosen a barber, show services
# 3. service_selected - User has chosen a service, show available slots
# 4. slot_selected - User has chosen a time slot, ask for name, phone number, AND email address (all three together)
# 5. collecting_details - Currently collecting customer information (name, phone, email)
# 6. details_complete - All info collected, ask for final confirmation
# 7. confirming_booking - Final confirmation before booking (will create Google Calendar event)

# RESPONSE GUIDELINES:
# - Be conversational and friendly like a salon receptionist
# - Use emojis sparingly (1-2 per response maximum)
# - Keep responses concise and clear
# - Always acknowledge what the user has already provided
# - Guide them to the next step smoothly
# - Mention that appointments will be added to Google Calendar
# - If all booking details are complete, ask for confirmation to book

# CURRENT STEP SPECIFIC INSTRUCTIONS:
# - If booking_step is "initial": Help user choose a barber or show all barbers
# - If booking_step is "barber_selected": Show services for selected barber
# - If booking_step is "service_selected": Show available time slots for the barber
# - If booking_step is "slot_selected": Ask for all three: "I'll need your full name, phone number, and email address to complete the booking"
# - If booking_step is "collecting_details": Continue collecting missing information (name, phone, email) - mention what's still needed
# - If booking_step is "details_complete": Show booking summary and ask for confirmation (mention Google Calendar)
# - If all details are provided but not yet confirmed: Ask "Shall I confirm this booking and add it to Google Calendar?"

# CUSTOMER DETAILS COLLECTION:
# When in "slot_selected" step, you must ask for ALL THREE pieces of information at once:
# - Full name
# - Phone number  
# - Email address
# Say something like: "Perfect! I'll need your full name, phone number, and email address to complete the booking."

# EMAIL IS MANDATORY: Never proceed to booking without collecting a valid email address.

# CURRENT USER INPUT: {user_input}

# Provide a helpful response that moves the booking process forward efficiently:"""

#         return system_prompt

#     def extract_booking_info(self, user_input: str):
#         """Extract booking information from user input and update context"""
#         user_input_lower = user_input.lower()
        
#         # Extract barber ID or name
#         id_match = re.search(r'\bid\s*(\d+)', user_input_lower)
#         if id_match:
#             barber_id = int(id_match.group(1))
#             barber = self.get_barber_by_id(barber_id)
#             if barber:
#                 self.context["selected_barber_id"] = barber_id
#                 self.context["selected_barber"] = barber["name"]
#                 if self.context["booking_step"] == "initial":
#                     self.context["booking_step"] = "barber_selected"
        
#         # Check for barber names
#         barbers = self.get_barbers_data()
#         for barber in barbers:
#             if barber["name"].lower() in user_input_lower:
#                 self.context["selected_barber"] = barber["name"]
#                 self.context["selected_barber_id"] = barber["id"]
#                 if self.context["booking_step"] == "initial":
#                     self.context["booking_step"] = "barber_selected"
#                 break
        
#         # Extract service selection
#         if self.context.get("selected_barber_id") and not self.context.get("selected_service"):
#             available_services = self.get_barber_services(self.context["selected_barber_id"])
#             for service in available_services:
#                 if service.lower() in user_input_lower:
#                     self.context["selected_service"] = service
#                     self.context["booking_step"] = "service_selected"
#                     break
        
#         # Extract time slot selection - improved pattern matching
#         if self.context.get("selected_barber_id") and not self.context.get("selected_slot"):
#             # Look for date and time patterns
#             datetime_patterns = [
#                 r'(\d{4}-\d{2}-\d{2}\s+(?:at\s+)?\d{1,2}:\d{2}\s+[AaPp][Mm])',
#                 r'(\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}\s+[AaPp][Mm])',
#                 r'(\d{4}-\d{1,2}-\d{1,2}\s+(?:at\s+)?\d{1,2}:\d{2}\s+[AaPp][Mm])'
#             ]
            
#             for pattern in datetime_patterns:
#                 datetime_match = re.search(pattern, user_input, re.IGNORECASE)
#                 if datetime_match:
#                     selected_slot = datetime_match.group(1).strip()
#                     # Normalize the format
#                     selected_slot = re.sub(r'\s+at\s+', ' ', selected_slot, flags=re.IGNORECASE)
                    
#                     # Check if this slot is available for the selected barber
#                     available_slots = self.get_available_slots(self.context["selected_barber_id"])
#                     if selected_slot in available_slots:
#                         self.context["selected_slot"] = selected_slot
#                         self.context["booking_step"] = "slot_selected"
#                         break
        
#         # Extract customer name - improved patterns
#         if self.context["booking_step"] in ["slot_selected", "collecting_details"] and not self.context.get("customer_name"):
#             name_patterns = [
#                 r'name[:\s]+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
#                 r'my name is\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
#                 r'i am\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
#                 r'name\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
#                 r'^([A-Za-z]+)\s*,',  # Name at start followed by comma
#             ]
            
#             for pattern in name_patterns:
#                 match = re.search(pattern, user_input_lower)
#                 if match:
#                     self.context["customer_name"] = match.group(1).title()
#                     break
        
#         # Extract phone numbers
#         if self.context["booking_step"] in ["slot_selected", "collecting_details"] and not self.context.get("customer_phone"):
#             phone_patterns = [
#                 r'phone(?:\s+number)?[:\s]*(\d+)',
#                 r'number[:\s]*(\d+)',
#                 r'(\d{10,})',  # Any 10+ digit number
#             ]
            
#             for pattern in phone_patterns:
#                 phone_match = re.search(pattern, user_input)
#                 if phone_match:
#                     phone_number = phone_match.group(1)
#                     if len(phone_number) >= 10:  # Valid phone number
#                         self.context["customer_phone"] = phone_number
#                         break
        
#         # Extract email address
#         if self.context["booking_step"] in ["slot_selected", "collecting_details"] and not self.context.get("customer_email"):
#             email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#             email_match = re.search(email_pattern, user_input)
#             if email_match:
#                 self.context["customer_email"] = email_match.group(0)
        
#         # Update booking step logic
#         if self.context["booking_step"] == "slot_selected":
#             # Move to collecting_details if we don't have all info yet
#             if not (self.context.get("customer_name") and 
#                    self.context.get("customer_phone") and
#                    self.context.get("customer_email")):
#                 self.context["booking_step"] = "collecting_details"
        
#         # Update booking step when all details are collected
#         if (self.context.get("customer_name") and 
#             self.context.get("customer_phone") and
#             self.context.get("customer_email") and
#             self.context.get("selected_slot") and 
#             self.context.get("selected_service") and 
#             self.context.get("selected_barber_id")):
            
#             if self.context["booking_step"] in ["slot_selected", "collecting_details"]:
#                 self.context["booking_step"] = "details_complete"

#     # ---------- AI-Powered Response Generation ----------
#     def generate_response(self, user_input: str) -> str:
#         """Generate AI-powered response using RAG approach"""
#         try:
#             # Add user input to conversation history
#             self.context["conversation_history"].append(f"User: {user_input}")
            
#             # Extract booking information from user input
#             self.extract_booking_info(user_input)
            
#             # Handle booking confirmation - check for confirmation keywords
#             if self.context["booking_step"] == "details_complete":
#                 confirmation_keywords = ["yes", "confirm", "book", "proceed", "ok", "sure", "please"]
#                 if any(keyword in user_input.lower() for keyword in confirmation_keywords):
#                     # Attempt to book the appointment
#                     booking_result = self.book_appointment(
#                         self.context["selected_barber_id"],
#                         self.context["selected_service"],
#                         self.context["selected_slot"],
#                         self.context["customer_name"],
#                         self.context["customer_phone"],
#                         self.context["customer_email"]
#                     )
                    
#                     if booking_result["success"]:
#                         calendar_info = ""
#                         if booking_result.get("calendar_event_id"):
#                             calendar_info = f"\n\n📅 Google Calendar: Your appointment has been added to Google Calendar!"
#                             if booking_result.get("calendar_link"):
#                                 calendar_info += f"\n🔗 Calendar Link: {booking_result['calendar_link']}"
                        
#                         response = f"🎉 Perfect! Your appointment has been successfully booked and added to Google Calendar!\n\n📅 Booking Confirmation:\n- Barber: {self.context['selected_barber']}\n- Service: {self.context['selected_service']}\n- Date & Time: {self.context['selected_slot']}\n- Customer: {self.context['customer_name']}\n- Phone: {self.context['customer_phone']}\n- Email: {self.context['customer_email']}"
                        
#                         response += calendar_info + "\n\nWe look forward to seeing you! 💇‍♂️"
                        
#                         self.context["booking_confirmed"] = True
#                         self.context["booking_step"] = "completed"
#                     else:
#                         error_msg = booking_result.get("error", "Unknown error occurred")
#                         response = f"❌ Sorry, there was an issue booking your appointment: {error_msg}. Please try again or contact us directly."
#                         self.context["booking_failed"] = True
                    
#                     # Add response to history and return
#                     self.context["conversation_history"].append(f"Assistant: {response}")
#                     return response
            
#             # Create dynamic prompt with all context
#             prompt = self.create_dynamic_prompt(user_input, self.context)
            
#             # Generate response using Gemini
#             response = self.model.generate_content(prompt)
#             ai_response = response.text.strip()
            
#             # Add specific step-based enhancements
#             if self.context["booking_step"] == "details_complete":
#                 # Show summary and ask for confirmation
#                 ai_response = f"Perfect! I have all the details for your appointment:\n\n📋 Booking Summary:\n- Barber: {self.context['selected_barber']}\n- Service: {self.context['selected_service']}\n- Time: {self.context['selected_slot']}\n- Name: {self.context['customer_name']}\n- Phone: {self.context['customer_phone']}\n- Email: {self.context['customer_email']}\n\n📅 Your appointment will be automatically added to Google Calendar upon confirmation.\n\nShall I confirm this booking for you? Just say 'yes' or 'confirm' to proceed! ✅"
            
#             # Ensure we always ask for name, phone and email together when details are missing
#             if self.context.get("booking_step") in ["slot_selected", "collecting_details"]:
#                 missing = []
#                 if not self.context.get("customer_name"):
#                     missing.append("full name")
#                 if not self.context.get("customer_phone"):
#                     missing.append("phone number")
#                 if not self.context.get("customer_email"):
#                     missing.append("email address")
#                 if missing:
#                     if len(missing) == 3:
#                         ask = "your full name, phone number, and email address"
#                     elif len(missing) == 2:
#                         ask = f"your {missing[0]} and {missing[1]}"
#                     else:
#                         ask = f"your {missing[0]}"
#                     ai_response = (
#                         "Perfect! To complete your booking, please provide " + ask + ".\n"
#                         "Example: 'Name Ali, phone 03001234567, email ali@example.com'"
#                     )
            
#             # Add AI response to conversation history
#             self.context["conversation_history"].append(f"Assistant: {ai_response}")
            
#             # Keep only last 20 exchanges in history
#             if len(self.context["conversation_history"]) > 20:
#                 self.context["conversation_history"] = self.context["conversation_history"][-20:]
            
#             return ai_response
            
#         except Exception as e:
#             logger.error(f"Error generating response: {str(e)}")
#             return f"I apologize, but I'm having trouble processing your request right now. Please try asking: 'show all barbers' or 'help me book an appointment'. Error: {str(e)}"

#     # ---------- Reset ----------
#     def reset_conversation(self):
#         """Reset conversation context"""
#         self.context = {
#             "booking_step": "initial",
#             "selected_barber": None,
#             "selected_barber_id": None,
#             "selected_service": None,
#             "selected_slot": None,
#             "customer_name": None,
#             "customer_phone": None,
#             "customer_email": None,
#             "booking_confirmed": False,
#             "booking_failed": False,
#             "calendar_event_id": None,
#             "conversation_history": []
#         }
#         self.barbers_cache = None  # Clear cache
#         logger.info("Conversation context has been reset.")


import os
import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
import json
import re
import requests

# Load environment variables
load_dotenv(".env1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BarberChatbot")


class BarberChatbot:
    def __init__(self):
        # Initialize Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("❌ SUPABASE_URL or SUPABASE_KEY is missing in .env")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize Gemini AI
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("❌ GEMINI_API_KEY is missing in .env")
        
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # N8N Webhook URL from environment
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
        if not self.n8n_webhook_url:
            raise ValueError("❌ N8N_WEBHOOK_URL is missing in .env1")
        
        # Context for session
        self.context = {
            "booking_step": "initial",
            "selected_barber": None,
            "selected_barber_id": None,
            "selected_service": None,
            "selected_slot": None,
            "customer_name": None,
            "customer_phone": None,
            "customer_email": None,
            "booking_confirmed": False,
            "booking_failed": False,
            "calendar_event_id": None,
            "conversation_history": []
        }
        
        # Cache for barber data
        self.barbers_cache = None

    # ---------- Database Methods ----------
    def get_barbers_data(self) -> List[Dict[str, Any]]:
        """Fetch all barbers from Supabase with caching"""
        if self.barbers_cache is not None:
            return self.barbers_cache
            
        try:
            logger.info("Fetching all barbers from Supabase")
            response = self.client.table("Barber_bookings").select("*").execute()
            data = response.data
            logger.info(f"Raw Supabase response: {data}")

            if not data:
                return []

            # Normalize data
            barbers = []
            for row in data:
                barber_info = {
                    "id": row.get("id"),
                    "name": row.get("Barber", "").strip(),
                    "services": row.get("Services", ""),
                    "slots": row.get("Available Slots", [])
                }
                barbers.append(barber_info)
            
            self.barbers_cache = barbers
            return barbers
        except Exception as e:
            logger.error(f"Error fetching barbers: {str(e)}")
            return []

    def get_barber_by_id(self, barber_id: int) -> Optional[Dict[str, Any]]:
        """Get specific barber by ID"""
        barbers = self.get_barbers_data()
        for barber in barbers:
            if barber["id"] == barber_id:
                return barber
        return None

    def get_barber_by_name(self, barber_name: str) -> Optional[Dict[str, Any]]:
        """Get specific barber by name"""
        barbers = self.get_barbers_data()
        barber_name_lower = barber_name.lower().strip()
        for barber in barbers:
            if barber["name"].lower() == barber_name_lower:
                return barber
        return None

    def get_available_slots(self, barber_id: int) -> List[str]:
        """Fetch available slots for a specific barber"""
        barber = self.get_barber_by_id(barber_id)
        if not barber:
            return []
        
        slots = barber["slots"]  # Direct access instead of .get()
        if isinstance(slots, list):
            return [self.format_datetime(slot) for slot in slots]
        return []

    def get_barber_services(self, barber_id: int) -> List[str]:
        """Get services offered by a specific barber"""
        barber = self.get_barber_by_id(barber_id)
        if not barber:
            return []
        
        services = barber["services"]  # Direct access instead of .get()
        if isinstance(services, str):
            return [service.strip() for service in services.split(",") if service.strip()]
        return []

    def format_datetime(self, datetime_str: str) -> str:
        """Format datetime string to readable format"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %I:%M %p")
        except:
            return datetime_str

    def call_n8n_webhook(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call n8n webhook to create booking and Google Calendar event"""
        try:
            logger.info(f"Calling n8n webhook with data: {booking_data}")
            
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
                    "description": f"Customer: {booking_data['customer_name']}\nPhone: {booking_data['customer_phone']}\nEmail: {booking_data['customer_email']}\nService: {booking_data['service']}\nBarber: {booking_data['barber_name']}",
                    "start_time": booking_data["appointment_time"],
                    "duration_minutes": 60,  # Default 1 hour appointment
                    "attendees": [booking_data.get("customer_email", "")]
                }
            }
            
            # Make the API call
            response = requests.post(
                self.n8n_webhook_url,
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "BarberSalonChatbot/1.0"
                },
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse response - handle different response formats
            result = {}
            if response.content:
                try:
                    raw_response = response.json()
                    logger.info(f"n8n webhook response: {raw_response}")
                    
                    # Handle list response format (like your current n8n setup)
                    if isinstance(raw_response, list) and len(raw_response) > 0:
                        # Extract calendar link from the response text
                        if 'content' in raw_response[0] and 'parts' in raw_response[0]['content']:
                            response_text = raw_response[0]['content']['parts'][0].get('text', '')
                            # Extract calendar link from the email text
                            import re
                            calendar_link_match = re.search(r'https://www\.google\.com/calendar/event\?eid=([^\s]+)', response_text)
                            if calendar_link_match:
                                result['calendar_link'] = calendar_link_match.group(0)
                        
                        # Generate a pseudo event ID from the response
                        result['calendar_event_id'] = f"booking_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        result['booking_id'] = result['calendar_event_id']
                    
                    # Handle standard JSON response format  
                    elif isinstance(raw_response, dict):
                        result = raw_response
                        
                except json.JSONDecodeError:
                    logger.warning("Could not parse JSON response, treating as success")
                    result = {}
            
            # Always return success if the HTTP request succeeded
            return {
                "success": True,
                "message": "Booking created and added to Google Calendar",
                "calendar_event_id": result.get("calendar_event_id", f"booking_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                "booking_id": result.get("booking_id", f"booking_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                "calendar_link": result.get("calendar_link", "Calendar event created successfully")
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

    def book_appointment(self, barber_id: int, service: str, slot: str, customer_name: str, customer_phone: str, customer_email: str = "") -> Dict[str, Any]:
        """Book appointment in the database and Google Calendar via n8n webhook"""
        try:
            barber = self.get_barber_by_id(barber_id)
            if not barber:
                return {"success": False, "error": "Barber not found"}
            
            # Prepare booking data
            booking_data = {
                "barber_id": barber_id,
                "barber_name": barber["name"],
                "service": service,
                "appointment_time": slot,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "status": "confirmed",
                "created_at": datetime.now().isoformat()
            }
            
            # Call n8n webhook to create booking and calendar event
            webhook_result = self.call_n8n_webhook(booking_data)
            
            if not webhook_result["success"]:
                return webhook_result
            
            # Update available slots in Supabase (remove booked slot)
            try:
                current_slots = barber["slots"]
                updated_slots = []
                
                for existing_slot in current_slots:
                    formatted_slot = self.format_datetime(existing_slot)
                    if formatted_slot != slot:
                        updated_slots.append(existing_slot)
                
                # Update the barber's available slots in database
                update_response = self.client.table("Barber_bookings").update({
                    "Available Slots": updated_slots
                }).eq("id", barber_id).execute()
                
                # Check if update was successful - handle Supabase APIResponse properly
                if hasattr(update_response, 'data') and update_response.data:
                    logger.info("Successfully updated available slots")
                else:
                    logger.warning("Could not update available slots, but booking still successful")
                
            except Exception as slot_error:
                logger.error(f"Error updating available slots: {str(slot_error)}")
                # Don't fail the booking if slot update fails, just log it
            
            # Clear cache to force refresh
            self.barbers_cache = None
            
            # Store calendar event ID in context
            self.context["calendar_event_id"] = webhook_result.get("calendar_event_id")
            
            return {
                "success": True,
                "message": "Appointment booked successfully and added to Google Calendar",
                "calendar_event_id": webhook_result.get("calendar_event_id"),
                "booking_id": webhook_result.get("booking_id"),
                "calendar_link": webhook_result.get("calendar_link")
            }
            
        except Exception as e:
            logger.error(f"Error booking appointment: {str(e)}")
            return {"success": False, "error": str(e)}

    # ---------- RAG Knowledge Base ----------
    def build_knowledge_base(self) -> str:
        """Build knowledge base from barber data"""
        barbers = self.get_barbers_data()
        
        knowledge = "BARBER SALON INFORMATION:\n\n"
        
        for barber in barbers:
            knowledge += f"Barber ID: {barber['id']}\n"
            knowledge += f"Barber Name: {barber['name']}\n"
            
            # Services
            services = self.get_barber_services(barber['id'])
            knowledge += f"Services: {', '.join(services)}\n"
            
            # Available slots
            slots = self.get_available_slots(barber['id'])
            knowledge += f"Available Slots: {', '.join(slots[:10])}{'...' if len(slots) > 10 else ''}\n"
            knowledge += "---\n"
        
        return knowledge

    def create_dynamic_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Create dynamic prompt based on context and user input"""
        
        knowledge_base = self.build_knowledge_base()
        
        # Determine current booking step and create appropriate prompt
        booking_step = context.get('booking_step', 'initial')
        
        system_prompt = f"""
You are a friendly and helpful AI barber salon assistant. Your job is to help customers find barbers, services, and book appointments efficiently.

CURRENT SALON DATA:
{knowledge_base}

CURRENT BOOKING CONTEXT:
- Booking Step: {booking_step}
- Selected Barber: {context.get('selected_barber', 'None')} (ID: {context.get('selected_barber_id', 'None')})
- Selected Service: {context.get('selected_service', 'None')}
- Selected Slot: {context.get('selected_slot', 'None')}
- Customer Name: {context.get('customer_name', 'None')}
- Customer Phone: {context.get('customer_phone', 'None')}
- Customer Email: {context.get('customer_email', 'None')}

CRITICAL BOOKING FLOW RULES:
1. NEVER repeat information that has already been confirmed
2. NEVER ask for the same information twice
3. Move forward in the booking process, don't go backwards
4. When user provides all required info (barber, service, slot, name, phone, email), proceed to confirmation
5. DO NOT show available slots again if a slot has already been selected
6. Appointments will be automatically added to Google Calendar upon confirmation
7. ALWAYS ask for NAME, PHONE NUMBER, AND EMAIL ADDRESS together when collecting customer details - say "I'll need your full name, phone number, and email address"
8. EMAIL ADDRESS is REQUIRED - never proceed to booking without collecting the customer's email

BOOKING PROCESS STEPS:
1. initial - User asking general questions or starting conversation
2. barber_selected - User has chosen a barber, show services
3. service_selected - User has chosen a service, show available slots
4. slot_selected - User has chosen a time slot, ask for name, phone number, AND email address (all three together)
5. collecting_details - Currently collecting customer information (name, phone, email)
6. details_complete - All info collected, ask for final confirmation
7. confirming_booking - Final confirmation before booking (will create Google Calendar event)

RESPONSE GUIDELINES:
- Be conversational and friendly like a salon receptionist
- Use emojis sparingly (1-2 per response maximum)
- Keep responses concise and clear
- Always acknowledge what the user has already provided
- Guide them to the next step smoothly
- Mention that appointments will be added to Google Calendar
- If all booking details are complete, ask for confirmation to book

CURRENT STEP SPECIFIC INSTRUCTIONS:
- If booking_step is "initial": Help user choose a barber or show all barbers
- If booking_step is "barber_selected": Show services for selected barber
- If booking_step is "service_selected": Show available time slots for the barber
- If booking_step is "slot_selected": Ask for all three: "I'll need your full name, phone number, and email address to complete the booking"
- If booking_step is "collecting_details": Continue collecting missing information (name, phone, email) - mention what's still needed
- If booking_step is "details_complete": Show booking summary and ask for confirmation (mention Google Calendar)
- If all details are provided but not yet confirmed: Ask "Shall I confirm this booking and add it to Google Calendar?"

CUSTOMER DETAILS COLLECTION:
When in "slot_selected" step, you must ask for ALL THREE pieces of information at once:
- Full name
- Phone number  
- Email address
Say something like: "Perfect! I'll need your full name, phone number, and email address to complete the booking."

EMAIL IS MANDATORY: Never proceed to booking without collecting a valid email address.

CURRENT USER INPUT: {user_input}

Provide a helpful response that moves the booking process forward efficiently:"""

        return system_prompt

    def extract_booking_info(self, user_input: str):
        """Extract booking information from user input and update context"""
        user_input_lower = user_input.lower()
        
        # Extract barber ID or name
        id_match = re.search(r'\bid\s*(\d+)', user_input_lower)
        if id_match:
            barber_id = int(id_match.group(1))
            barber = self.get_barber_by_id(barber_id)
            if barber:
                self.context["selected_barber_id"] = barber_id
                self.context["selected_barber"] = barber["name"]
                if self.context["booking_step"] == "initial":
                    self.context["booking_step"] = "barber_selected"
        
        # Check for barber names
        barbers = self.get_barbers_data()
        for barber in barbers:
            if barber["name"].lower() in user_input_lower:
                self.context["selected_barber"] = barber["name"]
                self.context["selected_barber_id"] = barber["id"]
                if self.context["booking_step"] == "initial":
                    self.context["booking_step"] = "barber_selected"
                break
        
        # Extract service selection
        if self.context.get("selected_barber_id") and not self.context.get("selected_service"):
            available_services = self.get_barber_services(self.context["selected_barber_id"])
            for service in available_services:
                if service.lower() in user_input_lower:
                    self.context["selected_service"] = service
                    self.context["booking_step"] = "service_selected"
                    break
        
        # Extract time slot selection - improved pattern matching
        if self.context.get("selected_barber_id") and not self.context.get("selected_slot"):
            # Look for date and time patterns
            datetime_patterns = [
                r'(\d{4}-\d{2}-\d{2}\s+(?:at\s+)?\d{1,2}:\d{2}\s+[AaPp][Mm])',
                r'(\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}\s+[AaPp][Mm])',
                r'(\d{4}-\d{1,2}-\d{1,2}\s+(?:at\s+)?\d{1,2}:\d{2}\s+[AaPp][Mm])'
            ]
            
            for pattern in datetime_patterns:
                datetime_match = re.search(pattern, user_input, re.IGNORECASE)
                if datetime_match:
                    selected_slot = datetime_match.group(1).strip()
                    # Normalize the format
                    selected_slot = re.sub(r'\s+at\s+', ' ', selected_slot, flags=re.IGNORECASE)
                    
                    # Check if this slot is available for the selected barber
                    available_slots = self.get_available_slots(self.context["selected_barber_id"])
                    if selected_slot in available_slots:
                        self.context["selected_slot"] = selected_slot
                        self.context["booking_step"] = "slot_selected"
                        break
        
        # Extract customer name - improved patterns
        if self.context["booking_step"] in ["slot_selected", "collecting_details"] and not self.context.get("customer_name"):
            name_patterns = [
                r'name[:\s]+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
                r'my name is\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
                r'i am\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
                r'name\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
                r'^([A-Za-z]+)\s*,',  # Name at start followed by comma
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, user_input_lower)
                if match:
                    self.context["customer_name"] = match.group(1).title()
                    break
        
        # Extract phone numbers
        if self.context["booking_step"] in ["slot_selected", "collecting_details"] and not self.context.get("customer_phone"):
            phone_patterns = [
                r'phone(?:\s+number)?[:\s]*(\d+)',
                r'number[:\s]*(\d+)',
                r'(\d{10,})',  # Any 10+ digit number
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, user_input)
                if phone_match:
                    phone_number = phone_match.group(1)
                    if len(phone_number) >= 10:  # Valid phone number
                        self.context["customer_phone"] = phone_number
                        break
        
        # Extract email address
        if self.context["booking_step"] in ["slot_selected", "collecting_details"] and not self.context.get("customer_email"):
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, user_input)
            if email_match:
                self.context["customer_email"] = email_match.group(0)
        
        # Update booking step logic
        if self.context["booking_step"] == "slot_selected":
            # Move to collecting_details if we don't have all info yet
            if not (self.context.get("customer_name") and 
                   self.context.get("customer_phone") and
                   self.context.get("customer_email")):
                self.context["booking_step"] = "collecting_details"
        
        # Update booking step when all details are collected
        if (self.context.get("customer_name") and 
            self.context.get("customer_phone") and
            self.context.get("customer_email") and
            self.context.get("selected_slot") and 
            self.context.get("selected_service") and 
            self.context.get("selected_barber_id")):
            
            if self.context["booking_step"] in ["slot_selected", "collecting_details"]:
                self.context["booking_step"] = "details_complete"

    # ---------- AI-Powered Response Generation ----------
    def generate_response(self, user_input: str) -> str:
        """Generate AI-powered response using RAG approach"""
        try:
            # Add user input to conversation history
            self.context["conversation_history"].append(f"User: {user_input}")
            
            # Extract booking information from user input
            self.extract_booking_info(user_input)
            
            # Handle booking confirmation - check for confirmation keywords
            if self.context["booking_step"] == "details_complete":
                confirmation_keywords = ["yes", "confirm", "book", "proceed", "ok", "sure", "please"]
                if any(keyword in user_input.lower() for keyword in confirmation_keywords):
                    # Attempt to book the appointment
                    booking_result = self.book_appointment(
                        self.context["selected_barber_id"],
                        self.context["selected_service"],
                        self.context["selected_slot"],
                        self.context["customer_name"],
                        self.context["customer_phone"],
                        self.context["customer_email"]
                    )
                    
                    if booking_result["success"]:
                        calendar_info = ""
                        if booking_result.get("calendar_event_id"):
                            calendar_info = f"\n\n📅 Google Calendar: Your appointment has been added to Google Calendar!"
                            if booking_result.get("calendar_link"):
                                calendar_info += f"\n🔗 Calendar Link: {booking_result['calendar_link']}"
                        
                        response = f"🎉 Perfect! Your appointment has been successfully booked and added to Google Calendar!\n\n📅 Booking Confirmation:\n- Barber: {self.context['selected_barber']}\n- Service: {self.context['selected_service']}\n- Date & Time: {self.context['selected_slot']}\n- Customer: {self.context['customer_name']}\n- Phone: {self.context['customer_phone']}\n- Email: {self.context['customer_email']}"
                        
                        response += calendar_info + "\n\nWe look forward to seeing you! 💇‍♂️"
                        
                        self.context["booking_confirmed"] = True
                        self.context["booking_step"] = "completed"
                    else:
                        error_msg = booking_result.get("error", "Unknown error occurred")
                        response = f"❌ Sorry, there was an issue booking your appointment: {error_msg}. Please try again or contact us directly."
                        self.context["booking_failed"] = True
                    
                    # Add response to history and return
                    self.context["conversation_history"].append(f"Assistant: {response}")
                    return response
            
            # Create dynamic prompt with all context
            prompt = self.create_dynamic_prompt(user_input, self.context)
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            ai_response = response.text.strip()
            
            # Add specific step-based enhancements
            if self.context["booking_step"] == "details_complete":
                # Show summary and ask for confirmation
                ai_response = f"Perfect! I have all the details for your appointment:\n\n📋 Booking Summary:\n- Barber: {self.context['selected_barber']}\n- Service: {self.context['selected_service']}\n- Time: {self.context['selected_slot']}\n- Name: {self.context['customer_name']}\n- Phone: {self.context['customer_phone']}\n- Email: {self.context['customer_email']}\n\n📅 Your appointment will be automatically added to Google Calendar upon confirmation.\n\nShall I confirm this booking for you? Just say 'yes' or 'confirm' to proceed! ✅"
            
            # Ensure we always ask for name, phone and email together when details are missing
            if self.context.get("booking_step") in ["slot_selected", "collecting_details"]:
                missing = []
                if not self.context.get("customer_name"):
                    missing.append("full name")
                if not self.context.get("customer_phone"):
                    missing.append("phone number")
                if not self.context.get("customer_email"):
                    missing.append("email address")
                if missing:
                    if len(missing) == 3:
                        ask = "your full name, phone number, and email address"
                    elif len(missing) == 2:
                        ask = f"your {missing[0]} and {missing[1]}"
                    else:
                        ask = f"your {missing[0]}"
                    ai_response = (
                        "Perfect! To complete your booking, please provide " + ask + ".\n"
                        "Example: 'Name Ali, phone 03001234567, email ali@example.com'"
                    )
            
            # Add AI response to conversation history
            self.context["conversation_history"].append(f"Assistant: {ai_response}")
            
            # Keep only last 20 exchanges in history
            if len(self.context["conversation_history"]) > 20:
                self.context["conversation_history"] = self.context["conversation_history"][-20:]
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I apologize, but I'm having trouble processing your request right now. Please try asking: 'show all barbers' or 'help me book an appointment'. Error: {str(e)}"

    # ---------- Reset ----------
    def reset_conversation(self):
        """Reset conversation context"""
        self.context = {
            "booking_step": "initial",
            "selected_barber": None,
            "selected_barber_id": None,
            "selected_service": None,
            "selected_slot": None,
            "customer_name": None,
            "customer_phone": None,
            "customer_email": None,
            "booking_confirmed": False,
            "booking_failed": False,
            "calendar_event_id": None,
            "conversation_history": []
        }
        self.barbers_cache = None  # Clear cache
        logger.info("Conversation context has been reset.")