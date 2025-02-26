from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from db_connection import connect_db
from cohere_ai import generate_ai_response
from googletrans import Translator
import re

app = Flask(__name__)
translator = Translator()

def detect_language(text):
    """Detects the language of the input text."""
    try:
        detected_lang = translator.detect(text)
        return detected_lang.lang
    except Exception as e:
        print(f"⚠️ Language detection failed: {e}")
        return "en"

def translate_text(text, target_language):
    """Translates text to the target language."""
    try:
        translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        print(f"⚠️ Translation failed: {e}")
        return text  

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

def detect_sentiment(text):
    """Basic sentiment analysis to determine tone."""
    positive_words = ["best", "amazing", "great", "love", "luxury", "excited", "happy", "wonderful"]
    negative_words = ["bad", "disappointed", "worst", "terrible", "upset", "hate", "frustrated"]

    text_lower = text.lower()

    if any(word in text_lower for word in positive_words):
        return "positive"
    elif any(word in text_lower for word in negative_words):
        return "negative"
    return "neutral"

def add_emotion(response, user_message):
    """Enhances responses with emotion and personality."""
    sentiment = detect_sentiment(user_message)

    if sentiment == "positive":
        response = "😃 " + response + " Sounds like you're excited! 🎉"
    elif sentiment == "negative":
        response = "😞 " + response + " Sorry about that! Let me find something better for you. 🙏"
    else:
        response = "😊 " + response

    if "recommend" in user_message.lower():
        response += "\n🤖 Hmm... If I had legs, I’d run straight to this one: [Hotel Name]"
    elif "romantic" in user_message.lower():
        response += "\n💕 Love is in the air! Here are some dreamy places for your getaway. 😘"
    elif "adventure" in user_message.lower():
        response += "\n🏄‍♂️ Ready for an adventure? These places will get your adrenaline pumping! 🚀"

    return response

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
    sender_number = request.values.get("From", "")

    print(f"\n📥 [Step 0] Incoming Message from {sender_number}: {incoming_msg}")

    detected_language = detect_language(incoming_msg)
    print(f"🌍 Detected Language: {detected_language}")

    if detected_language != "en":
        incoming_msg = translate_text(incoming_msg, "en")
        print(f"🔄 Translated to English: {incoming_msg}")

    location, category, subcategory = extract_query_details(incoming_msg)
    
    if location and category:
        print(f"🗺 Extracted Location: {location}, Category: {category}, Subcategory: {subcategory}")
        bot_reply = get_response(location, category, subcategory)
    else:
        bot_reply = "Hey, I'm Nuru👩‍💻, your AI travel assistant. How can I help?"

    bot_reply = add_emotion(bot_reply, incoming_msg)

    if detected_language != "en":
        bot_reply = translate_text(bot_reply, detected_language)
        print(f"🔄 Translated Reply to {detected_language}: {bot_reply}")

    print(f"📤 [Step 6] Sending Response to WhatsApp...")
    twilio_response = MessagingResponse()
    twilio_response.message(bot_reply)

    print("✅ [Step 7] Message Sent Successfully!")
    return str(twilio_response)

if __name__ == "__main__":
    print("\n🚀 Starting Multilingual WhatsApp Travel Chatbot with Emotion & Humor...")
    app.run(host="0.0.0.0", port=5000, debug=True)
