import streamlit as st
from chatbot1 import BarberChatbot
import os
from dotenv import load_dotenv
import json
import requests

# Load env
load_dotenv(".env1")

st.set_page_config(
    page_title="💇‍♂️ Barber Salon Chatbot", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI with improved contrast
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .chat-message {
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        max-width: 85%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
    }
    .user-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        margin-left: auto;
        text-align: right;
        color: white;
        font-weight: 500;
    }
    .bot-message {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        margin-right: auto;
        color: #2c3e50;
        border-left: 4px solid #667eea;
    }
    .status-card {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 500;
    }
    .success-card {
        background: linear-gradient(135deg, #d4edda 0%, #c8e6c9 100%);
        border: 2px solid #4caf50;
        color: #2e7d32;
    }
    .error-card {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border: 2px solid #f44336;
        color: #c62828;
    }
    .warning-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #ffc107;
        color: #856404;
    }
    .stTextInput > div > div > input {
        background-color: white;
        color: #2c3e50;
        border: 2px solid #667eea;
        border-radius: 10px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .booking-step {
        background: linear-gradient(135deg, #fef9e7 0%, #fff3cd 100%);
        border: 2px solid #ffc107;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .calendar-info {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border: 2px solid #4caf50;
        color: #2e7d32;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Init Chatbot ----------
@st.cache_resource
def init_chatbot():
    try:
        return BarberChatbot()
    except Exception as e:
        st.error(f"Failed to initialize chatbot: {str(e)}")
        return None

chatbot = init_chatbot()

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chatbot_context = chatbot.context.copy() if chatbot else {}

# ---------- Header ----------
st.markdown("""
<div class="main-header">
    <h1>💇‍♂️ AI Barber Salon Assistant</h1>
    <p>Your intelligent booking companion with Google Calendar integration</p>
    <small>Powered by RAG, LangChain & n8n Automation</small>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("🔧 System Status")
    
    # Test connection button
    if st.button("🔄 Test Connection", key="test_conn"):
        if chatbot:
            with st.spinner("Testing connection..."):
                barbers = chatbot.get_barbers_data()
                if barbers:
                    st.markdown(f"""
                    <div class="status-card success-card">
                        <strong>✅ Connected Successfully</strong><br>
                        Found {len(barbers)} barbers in database
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show barber summary
                    st.subheader("📋 Barber Summary")
                    for barber in barbers:
                        services_count = len(chatbot.get_barber_services(barber['id']))
                        slots_count = len(chatbot.get_available_slots(barber['id']))
                        st.write(f"**{barber['name']}** (ID: {barber['id']}) - {services_count} services, {slots_count} slots")
                else:
                    st.markdown("""
                    <div class="status-card error-card">
                        <strong>❌ No Data Found</strong><br>
                        Connected but no barbers found
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.error("❌ Chatbot not initialized")

    # Test n8n webhook
    if st.button("🔗 Test n8n Webhook", key="test_webhook"):
        with st.spinner("Testing n8n webhook..."):
            try:
                test_payload = {
                    "event_type": "test_connection",
                    "booking_details": {
                        "barber_name": "Test Barber",
                        "service": "Test Service",
                        "appointment_time": "2024-01-01 10:00 AM",
                        "customer_name": "Test Customer",
                        "customer_phone": "1234567890",
                        "customer_email": "test@test.com"
                    },
                    "calendar_event": {
                        "summary": "Test Appointment",
                        "description": "Test booking",
                        "start_time": "2024-01-01 10:00 AM"
                    }
                }
                
                response = requests.post(
                    chatbot.n8n_webhook_url,
                    json=test_payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.markdown("""
                    <div class="status-card success-card">
                        <strong>✅ n8n Webhook Working</strong><br>
                        Calendar integration ready
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    body = response.text
                    extra_hint = ""
                    try:
                        j = response.json()
                        if j.get("code") == 404 and "webhook" in j.get("message", "").lower():
                            extra_hint = "<br><small>Tip: In n8n, activate the workflow to use the Production URL (/webhook/...) or click 'Execute workflow' and use the Test URL (/webhook-test/...). Ensure the webhook path matches N8N_WEBHOOK_URL.</small>"
                    except Exception:
                        pass
                    st.markdown(f"""
                    <div class="status-card warning-card">
                        <strong>⚠️ Webhook Response: {response.status_code}</strong><br>
                        {body[:300] + ('...' if len(body) > 300 else '')}
                        {extra_hint}
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.markdown(f"""
                <div class="status-card error-card">
                    <strong>❌ Webhook Test Failed</strong><br>
                    {str(e)}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Environment status
    st.subheader("🌐 Configuration Status")
    
    configs = [
        ("Supabase URL", os.getenv("SUPABASE_URL")),
        ("Supabase Key", os.getenv("SUPABASE_KEY")),
        ("Gemini API Key", os.getenv("GEMINI_API_KEY")),
        ("n8n Webhook", chatbot.n8n_webhook_url if chatbot else None)
    ]
    
    for config_name, config_value in configs:
        if config_value:
            st.markdown(f"""
            <div class="status-card success-card">
                ✅ {config_name} configured
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-card error-card">
                ❌ {config_name} missing
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Booking progress tracker
    if chatbot and chatbot.context.get("booking_step") != "initial":
        st.subheader("📋 Booking Progress")
        
        booking_steps = {
            "initial": "🏁 Starting",
            "barber_selected": "👨‍💼 Barber Selected", 
            "service_selected": "✂️ Service Chosen",
            "slot_selected": "📅 Time Picked",
            "collecting_details": "📝 Getting Details",
            "details_complete": "🔍 Ready to Confirm",
            "confirming_booking": "⏳ Creating Calendar Event",
            "completed": "🎉 Booked & Calendared"
        }
        
        current_step = chatbot.context.get("booking_step", "initial")
        
        for step, label in booking_steps.items():
            if step == current_step:
                st.markdown(f"**➤ {label}**")
            elif current_step in list(booking_steps.keys())[list(booking_steps.keys()).index(step):]:
                st.markdown(f"✅ {label}")
            else:
                st.markdown(f"⭕ {label}")
    
    # Show calendar event info if available
    if chatbot and chatbot.context.get("calendar_event_id"):
        st.markdown("---")
        st.subheader("📅 Calendar Info")
        st.markdown(f"""
        <div class="calendar-info">
            <strong>📅 Google Calendar Event Created</strong><br>
            Event ID: {chatbot.context.get("calendar_event_id")[:20]}...
        </div>
        """, unsafe_allow_html=True)
    
    # Context viewer
    if chatbot and st.checkbox("🔍 Show Context"):
        st.subheader("🧠 Current Context")
        context_display = {
            "Booking Step": st.session_state.chatbot_context.get("booking_step", "initial"),
            "Selected Barber": st.session_state.chatbot_context.get("selected_barber", "None"),
            "Barber ID": st.session_state.chatbot_context.get("selected_barber_id", "None"),
            "Selected Service": st.session_state.chatbot_context.get("selected_service", "None"),
            "Selected Slot": st.session_state.chatbot_context.get("selected_slot", "None"),
            "Customer Name": st.session_state.chatbot_context.get("customer_name", "None"),
            "Customer Phone": st.session_state.chatbot_context.get("customer_phone", "None"),
            "Customer Email": st.session_state.chatbot_context.get("customer_email", "None"),
            "Calendar Event ID": st.session_state.chatbot_context.get("calendar_event_id", "None")
        }
        
        for key, value in context_display.items():
            st.text(f"{key}: {value}")
    
    # Reset conversation
    if st.button("🔄 Reset Conversation", key="reset"):
        if chatbot:
            chatbot.reset_conversation()
            st.session_state.messages = []
            st.session_state.chatbot_context = chatbot.context.copy()
            st.success("✅ Conversation reset!")
            st.rerun()

# ---------- Main Chat Interface ----------
st.subheader("💬 Chat with AI Assistant")

# Chat container with custom styling
chat_container = st.container()

# Display conversation history
with chat_container:
    if not st.session_state.messages:
        # Welcome message
        st.markdown("""
        <div class="chat-message bot-message">
            <strong>🤖 Assistant:</strong> Welcome to our AI Barber Salon! I'm your smart assistant with Google Calendar integration. 
            I can help you with:
            <ul>
                <li>🧑‍💼 View all available barbers and their specialties</li>
                <li>✂️ Check services offered by specific barbers</li>
                <li>📅 See available appointment slots</li>
                <li>📋 Book appointments with automatic Google Calendar events</li>
                <li>📱 Send booking confirmations via n8n automation</li>
            </ul>
            Just tell me what you'd like to do, or try saying: <em>"Show me all barbers"</em> or <em>"I want to book an appointment"</em>
            <br><br>
            <strong>📅 New Feature:</strong> All confirmed appointments are automatically added to Google Calendar!
        </div>
        """, unsafe_allow_html=True)
    
    # Show message history
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>🧑 You:</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Format bot response with better line breaks and preserve formatting
            formatted_content = msg['content'].replace('\n', '<br>')
            
            # Check if message contains calendar confirmation
            if "Google Calendar" in msg['content'] and "successfully booked" in msg['content']:
                st.markdown(f"""
                <div class="chat-message bot-message calendar-info">
                    <strong>🤖 Assistant:</strong> {formatted_content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>🤖 Assistant:</strong> {formatted_content}
                </div>
                """, unsafe_allow_html=True)

# Show current booking step if in progress
if chatbot and chatbot.context.get("booking_step") not in ["initial", "completed"]:
    step_descriptions = {
        "barber_selected": "🎯 You've selected a barber! Now choose a service.",
        "service_selected": "✂️ Great choice! Now pick your preferred time slot.",
        "slot_selected": "📅 Perfect timing! Please provide your contact details.",
        "collecting_details": "📝 Almost there! Just need a few more details.",
        "details_complete": "✅ Ready to confirm and create Google Calendar event!",
        "confirming_booking": "⏳ Creating your Google Calendar appointment..."
    }
    
    current_step = chatbot.context.get("booking_step")
    if current_step in step_descriptions:
        st.markdown(f"""
        <div class="booking-step">
            <strong>{step_descriptions[current_step]}</strong>
        </div>
        """, unsafe_allow_html=True)

# ---------- Chat Input ----------
st.markdown("---")

# Create columns for input and examples
col1, col2 = st.columns([3, 1])

with col1:
    # Chat input
    if prompt := st.chat_input("Type your message here... 💬", key="main_input"):
        if not chatbot:
            st.error("❌ Chatbot not available. Please check configuration.")
        else:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Show typing indicator
            with st.spinner("🤔 AI is thinking..."):
                try:
                    # Generate response
                    response = chatbot.generate_response(prompt)
                    
                    # Add bot response
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Update context
                    st.session_state.chatbot_context = chatbot.context.copy()
                    
                    # Show success message if booking was completed
                    if chatbot.context.get("booking_confirmed"):
                        st.balloons()
                        st.success("🎉 Appointment booked successfully and added to Google Calendar!")
                    
                    # Show error if booking failed
                    elif chatbot.context.get("booking_failed"):
                        st.error("❌ Booking failed. Please try again or contact support.")
                    
                    # Auto-refresh to show updated messages
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Error processing your request: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.error("❌ An error occurred. Please try again.")
                    st.rerun()

with col2:
    st.subheader("💡 Quick Actions")
    
    # Quick action buttons
    quick_actions = [
        ("👥 Show All Barbers", "Show me all available barbers"),
        ("📅 Available Slots", "Show available appointment slots"),
        ("✂️ Services", "What services do you offer?"),
        ("📞 Book Appointment", "I want to book an appointment"),
        ("❓ Help", "How does booking work?")
    ]
    
    for label, message in quick_actions:
        if st.button(label, key=f"quick_{label}", use_container_width=True):
            if chatbot:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": message})
                
                # Generate response
                with st.spinner("🤔 Processing..."):
                    try:
                        response = chatbot.generate_response(message)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.session_state.chatbot_context = chatbot.context.copy()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.error("❌ Chatbot not available")

# ---------- Footer ----------
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666; font-size: 0.9em;">
    <p>🤖 <strong>AI Barber Salon Assistant</strong> | Powered by Gemini AI, Supabase & n8n</p>
    <p>📅 Automatic Google Calendar Integration | 🔒 Secure & Private</p>
    <p><small>Need help? Ask me anything about our barbers, services, or booking process!</small></p>
</div>
""", unsafe_allow_html=True)

# ---------- Auto-scroll to bottom ----------
js = '''
<script>
    var element = window.parent.document.querySelector('.main .block-container');
    element.scrollTop = element.scrollHeight;
</script>
'''
st.components.v1.html(js, height=0)