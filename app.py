from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from db_connection import connect_db
from cohere_ai import generate_ai_response
import re

app = Flask(__name__)

def extract_query_details(user_message):
    """Extracts location, category, and subcategory from user queries."""
    
    keywords = {
        "hotels": "Hotels", "resorts": "Resorts", "airbnbs": "Airbnbs",
        "restaurants": "Restaurants", "cafes": "Cafes", "fine dining": "Fine Dining",
        "cars": "Car Rentals", "bikes": "Bike Rentals", "ebikes": "Ebike Rentals"
    }
    
    location_match = re.search(r'in (.+)', user_message, re.IGNORECASE)
    location = location_match.group(1) if location_match else None
    
    category, subcategory = None, None
    words = user_message.lower().split()
    for word in words:
        if word in keywords:
            subcategory = keywords[word]
            if word in ["hotels", "resorts", "airbnbs"]:
                category = "Accommodation"
            elif word in ["restaurants", "cafes", "fine dining"]:
                category = "Eating"
            elif word in ["cars", "bikes", "ebikes"]:
                category = "Transport"
    
    return location, category, subcategory

def get_response(location, category, subcategory):
    """Fetches data from the database or falls back to AI."""
    
    print("\n🔄 [Step 1] Connecting to Database...")
    conn = connect_db()
    if not conn:
        print("❌ Database connection failed.")
        return "Database connection failed."

    cur = conn.cursor()
    print("🔍 [Step 2] Constructing SQL Query...")
    query = """
        SELECT DISTINCT p.name, p.description, p.price_range, p.rating, p.features 
        FROM places p
        JOIN subcategories s ON p.subcategory_id = s.id
        JOIN categories c ON s.category_id = c.id
        JOIN locations l ON c.location_id = l.id
        WHERE l.name ILIKE %s AND c.name ILIKE %s
    """
    params = [f"%{location}%", f"%{category}%"]

    if subcategory:
        query += " AND s.name ILIKE %s"
        params.append(f"%{subcategory}%")

    print(f"🚀 Executing SQL Query:\n{query}")
    print(f"📌 With Parameters: {params}")
    cur.execute(query, params)
    results = cur.fetchall()
    cur.close()
    conn.close()

    print(f"📊 [Step 3] Query Returned {len(results)} results.")

    if results:
        print("✅ [Step 4] Formatting Database Results...")
        formatted_results = []
        for row in results:
            name, description, price_range, rating, features = row
            formatted_results.append(
                f"🏨 {name}\n📌 {description}\n💰 {price_range}\n⭐ {rating}/5\n🔹 Features: {features}"
            )
        
        final_response = "\n\n".join(formatted_results)
        print(f"📩 [Step 5] Final Response:\n{final_response}")
        return final_response

    print("⚠️ No data found, falling back to AI response...")
    return generate_ai_response(f"Tell me about {subcategory or category} in {location}")

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    """Handles incoming messages and replies based on database or AI responses."""
    
    incoming_msg = request.values.get("Body", "").strip()
    print(f"\n📥 [Step 0] Incoming Message: {incoming_msg}")

    location, category, subcategory = extract_query_details(incoming_msg)
    
    if location and category:
        print(f"🗺 Extracted Location: {location}, Category: {category}, Subcategory: {subcategory}")
        bot_reply = get_response(location, category, subcategory)
    else:
        bot_reply = "I'm your travel assistant! Ask me about hotels, restaurants, or transport options in any city. 🌍"

    print(f"📤 [Step 6] Sending Response to WhatsApp...")
    twilio_response = MessagingResponse()
    twilio_response.message(bot_reply)

    print("✅ [Step 7] Message Sent Successfully!")
    return str(twilio_response)

if __name__ == "__main__":
    print("\n🚀 Starting WhatsApp Travel Chatbot...")
    app.run(host="0.0.0.0", port=5000, debug=True)
