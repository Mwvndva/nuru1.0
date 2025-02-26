from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from db_connection import connect_db
from cohere_ai import generate_ai_response

app = Flask(__name__)

def get_response(location, category, subcategory=None):
    """Fetches data from the database and falls back to AI if no data is found."""
    
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

    print(f"📊 [Step 3] Query Returned {len(results)} results.")

    cur.close()
    conn.close()

    if results:
        print("✅ [Step 4] Formatting Database Results...")
        formatted_results = []
        for row in results:
            name, description, price_range, rating, features = row
            formatted_results.append(
                f"🏨 {name}\n📌 {description}\n💰 {price_range}\n⭐ {rating}/5\n🔹 Features: {features}"
            )

        db_response = "\n\n".join(formatted_results)

        print("🤖 [Step 5] Fetching AI Response...")
        ai_response = generate_ai_response(f"Tell me about {category} in {location}")

        final_response = f"📌 **Database Results:**\n{db_response}\n\n🤖 **AI Response:**\n{ai_response}"
        print(f"📩 [Step 6] Final Response:\n{final_response}")

        return final_response

    print("⚠️ No data found, falling back to AI response...")
    return generate_ai_response(f"Tell me about {category} in {location}")

@app.route("/webhook", methods=["POST"])
def whatsapp_bot():
    """Handles incoming messages from Twilio and sends responses."""
    
    incoming_msg = request.values.get("Body", "").strip()
    print(f"\n📥 [Step 0] Incoming Message: {incoming_msg}")

    # Extract location, category, and subcategory (assumed processing)
    location = "Nairobi"  # Extracted dynamically
    category = "Accommodation"
    subcategory = "Hotels"

    print(f"🗺 Extracted Location: {location}, Category: {category}, Subcategory: {subcategory}")

    bot_reply = get_response(location, category, subcategory)

    print(f"📤 [Step 7] Sending Response to WhatsApp...")
    twilio_response = MessagingResponse()
    twilio_response.message(bot_reply)

    print("✅ [Step 8] Message Sent Successfully!")
    return str(twilio_response)

if __name__ == "__main__":
    print("\n🚀 Starting WhatsApp Travel Chatbot...")
    app.run(host="0.0.0.0", port=5000, debug=True)
