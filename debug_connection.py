import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_with_correct_table_name():
    """Test connection with the correct table name"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test with correct table name (capital B)
        response = supabase.table('Barber_bookings').select("*").execute()
        
        if response.data:
            print(f"🎉 SUCCESS! Found {len(response.data)} records in 'Barber_bookings' table")
            print("\nSample data:")
            for i, record in enumerate(response.data[:3]):
                print(f"  Record {i+1}: {record}")
            return True
        else:
            print("⚠️ Connection successful but no data found")
            return True
            
    except Exception as e:
        print(f"❌ Still failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Testing with correct table name 'Barber_bookings'...")
    test_with_correct_table_name()