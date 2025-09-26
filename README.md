# Barber Salon Chatbot System

A complete barber salon booking system with AI chatbot, built with FastAPI, Streamlit, and Supabase.

## 🏗️ System Architecture

```
User Interface (Streamlit) 
       ↓
AI Chatbot (Gemini + LangChain)
       ↓
FastAPI Endpoints
       ↓
Supabase Database
```

## 🚀 Features

- **AI-Powered Chatbot**: Natural conversation flow using Google Gemini
- **Dynamic Booking**: Real-time availability checking and booking
- **Barber Selection**: Browse barbers by ID with their services
- **Service Management**: View services offered by each barber
- **Time Slot Management**: Check and book available time slots
- **Customer Management**: Store customer information and booking history
- **RESTful API**: Complete FastAPI backend with all CRUD operations
- **Modern UI**: Beautiful Streamlit interface with real-time chat

## 📋 Prerequisites

- Python 3.8+
- Supabase account
- Google Gemini API key
- Git (optional)

## 🛠️ Installation & Setup

### Step 1: Clone/Download Files
Save all the provided files in your project directory:
```
barber-salon-chatbot/
├── app.py                 # Streamlit UI
├── chatbot.py            # RAG-based chatbot
├── endpoints.py          # FastAPI endpoints
├── requirements.txt      # Dependencies
├── .env                 # Environment variables
├── supabase_setup.sql   # Database setup
└── README.md           # This file
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Supabase Database

1. **Create a Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note your project URL and anon key

2. **Set Up Database Tables**:
   - Go to your Supabase dashboard
   - Navigate to SQL Editor
   - Copy and run the content from `supabase_setup.sql`
   - This will create the required tables and sample data

3. **Configure Database Access**:
   - Go to Settings → API
   - Make note of your URL and anon key
   - Ensure RLS is configured properly for your needs

### Step 4: Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key for use in your `.env` file

### Step 5: Configure Environment Variables

Edit the `.env` file with your actual credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# FastAPI Configuration
FASTAPI_HOST=localhost
FASTAPI_PORT=8000
```

### Step 6: Start the Services

1. **Start FastAPI Backend** (Terminal 1):
```bash
python endpoints.py
```
The API will be available at `http://localhost:8000`

2. **Start Streamlit Frontend** (Terminal 2):
```bash
streamlit run app.py
```
The web app will open at `http://localhost:8501`

## 🎯 Usage

### For Customers

1. **Start Conversation**: Type "Hi" or "I want to book an appointment"
2. **Choose Barber**: The bot will show available barbers with IDs (e.g., "I want barber ID 2")
3. **Select Service**: Choose from services offered by selected barber
4. **Pick Time**: Select from available time slots
5. **Provide Details**: Enter your name and phone number
6. **Confirmation**: Get booking confirmation with details

### Example Conversation Flow

```
User: Hi
Bot: Welcome to our barber salon! Here are our available barbers:
     🪒 Barber ID 1: John Smith
     Services: Hair Cut, Beard Trim, Shaving, Hair Wash
     
User: I want barber ID 2
Bot: Great choice! You've selected Mike Johnson (ID: 2)
     Here are the services offered:
     • Hair Cut
     • Mustache Styling
     • Hair Wash
     • Beard Trim
     
User: Hair Cut
Bot: Perfect! Available slots for today:
     1. 9:15 AM
     2. 9:45 AM
     3. 10:15 AM
     
User: 2
Bot: Great! Please provide your name and phone number.

User: John Doe 555-123-4567
Bot: 🎉 Booking Confirmed!
     • Booking ID: 123
     • Barber: Mike Johnson
     • Service: Hair Cut
     • Time: 9:45 AM
```

## 🔧 API Endpoints

### Barbers
- `GET /barbers` - Get all barbers
- `GET /barbers/{id}` - Get specific barber
- `GET /barbers/{id}/services` - Get barber services
- `GET /barbers/{id}/availability` - Get barber availability

### Bookings
- `POST /bookings` - Create new booking
- `GET /bookings/{phone}` - Get customer bookings
- `DELETE /bookings/{id}` - Cancel booking

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

## 📊 Database Schema

### Barbers Table
```sql
id (SERIAL PRIMARY KEY)
name (VARCHAR)
services (TEXT[])
availability (TEXT[])
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Bookings Table
```sql
id (SERIAL PRIMARY KEY)
barber_id (INTEGER, FK)
service (VARCHAR)
time_slot (VARCHAR)
customer_name (VARCHAR)
customer_phone (VARCHAR)
date (DATE)
status (VARCHAR)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

## 🎨 Customization

### Adding New Barbers
```sql
INSERT INTO barbers (name, services, availability) VALUES
('New Barber Name', 
 ARRAY['Service1', 'Service2', 'Service3'], 
 ARRAY['9:00 AM', '10:00 AM', '11:00 AM']);
```

### Modifying Services
Update the services array in the barbers table:
```sql
UPDATE barbers SET services = ARRAY['New Service List'] WHERE id = 1;
```

### Customizing Time Slots
Update the availability array:
```sql
UPDATE barbers SET availability = ARRAY['9:00 AM', '10:00 AM', '2:00 PM'] WHERE id = 1;
```

## 🔒 Security Considerations

1. **Environment Variables**: Never commit your `.env` file
2. **API Keys**: Keep your Gemini API key secure
3. **Database Access**: Configure Supabase RLS policies appropriately
4. **Input Validation**: The system includes basic validation, enhance as needed
5. **Rate Limiting**: Consider adding rate limiting for production

## 🚀 Deployment

### Local Development
Follow the setup instructions above.

### Production Deployment

1. **Backend (FastAPI)**:
   - Deploy to services like Railway, Render, or Heroku
   - Set environment variables on the hosting platform
   - Update CORS settings in `endpoints.py` if needed

2. **Frontend (Streamlit)**:
   - Deploy to Streamlit Cloud, Railway, or similar
   - Update API base URL in chatbot.py to point to your deployed backend

3. **Database**:
   - Supabase is already cloud-hosted
   - Ensure proper security policies are in place

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Failed**:
   - Check if FastAPI backend is running
   - Verify FASTAPI_HOST and FASTAPI_PORT in .env

2. **Database Connection Issues**:
   - Verify Supabase URL and key in .env
   - Check if database tables are created properly

3. **Gemini API Errors**:
   - Verify your Gemini API key
   - Check API quota and limits

4. **Module Import Errors**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

### Logs & Debugging

- FastAPI logs appear in the terminal where you run `python endpoints.py`
- Streamlit logs appear in the terminal where you run `streamlit run app.py`
- Check the browser console for frontend errors

## 📈 Future Enhancements

- [ ] SMS notifications for booking confirmations
- [ ] Email integration
- [ ] Payment processing
- [ ] Multi-language support
- [ ] Advanced booking rules (holidays, breaks)
- [ ] Customer reviews and ratings
- [ ] Loyalty program integration
- [ ] Mobile app version

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Happy Coding! 💇‍♂️✨**