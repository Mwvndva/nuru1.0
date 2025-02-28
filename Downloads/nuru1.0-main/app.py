from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from db_connection import connect_db
from cohere_ai import generate_ai_response
from googletrans import Translator
from serpapi import GoogleSearch
import re

app = Flask(__name__)
translator = Translator()

def google_search(query):
    """Fetches results from Google using SerpAPI."""
    API_KEY = "3a67406d46c0e4c4e4969ed0c93d305e26bb92eefaa0a3262127e2592c463825"  # Replace with your actual API key
    params = {
        "q": query,
        "engine": "google",
        "api_key": API_KEY
    }
    
    print(f"🌍 [Google Search] Searching for: {query}")
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])

        if not organic_results:
            print("⚠️ No Google search results found.")
            return "No external results found."

        response = []
        for result in organic_results[:5]:  # Limit to top 5 results
            title = result.get('title', 'No title')
            link = result.get('link', 'No link')
            response.append(f"🔎 {title} - {link}")

        print("✅ [Google Search] Results fetched successfully.")
        return "\n".join(response)
    
    except Exception as e:
        print(f"❌ [Google Search] API Error: {e}")
        return "Couldn't fetch external results at the moment."

def detect_language(text):
    """Detects the language of the input text."""
    try:
        detected_lang = translator.detect(text)
        print(f"🌍 [Language Detection] Detected language: {detected_lang.lang}")
        return detected_lang.lang
    except Exception as e:
        print(f"⚠️ [Language Detection] Error: {e}")
        return "en"

def translate_text(text, target_language):
    """Translates text to the target language."""
    try:
        translated = translator.translate(text, dest=target_language)
        print(f"🌍 [Translation] Translated '{text}' to '{translated.text}' in {target_language}.")
        return translated.text
    except Exception as e:
        print(f"⚠️ [Translation] Error: {e}")
        return text  

def extract_query_details(user_message):
    """Extracts location, category, and subcategory from user queries."""
    print(f"📝 [Query Extraction] Processing: '{user_message}'")
    
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
    
    print(f"✅ [Query Extraction] Location: {location}, Category: {category}, Subcategory: {subcategory}")
    return location, category, subcategory

def get_response(location, category, subcategory):
    """Fetches data from the database or falls back to AI/Google Search."""
    if not location or not category:
        print("⚠️ [Data Retrieval] Missing location or category.")
        return "I couldn't find enough details. Could you be more specific?"

    print("\n🔄 [Step 1] Connecting to Database...")
    conn = connect_db()
    if not conn:
        print("❌ [Database] Connection failed.")
        return "Database connection failed."

    cur = conn.cursor()
    print(f"🔍 [Step 2] Searching Database for {category}/{subcategory} in {location}...")

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

    try:
        cur.execute(query, params)
        results = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ [Database] Query Error: {e}")
        return "Database query error. Please try again."

    if results:
        print("✅ [Database] Found results. Formatting response...")
        formatted_results = []
        for row in results:
            name, description, price_range, rating, features = row
            formatted_results.append(
                f"🏨 {name}\n📌 {description}\n💰 {price_range}\n⭐ {rating}/5\n🔹 Features: {features}"
            )
        return "\n\n".join(formatted_results)

    print("⚠️ [Database] No data found, falling back to Google Search...")
    return google_search(f"{subcategory or category} in {location}")

def add_emotion(response, user_message):
    """Enhances responses with emotion and personality."""
    sentiment = "neutral"
    
    if "thank" in user_message.lower() or "great" in user_message.lower():
        sentiment = "positive"
    elif "bad" in user_message.lower() or "worst" in user_message.lower():
        sentiment = "negative"

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

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender_number = request.values.get("From", "")

    print(f"\n📥 [Incoming Message] '{incoming_msg}' from {sender_number}")
    detected_language = detect_language(incoming_msg)

    if detected_language != "en":
        incoming_msg = translate_text(incoming_msg, "en")
    
    location, category, subcategory = extract_query_details(incoming_msg)
    
    if location and category:
        bot_reply = get_response(location, category, subcategory)
    else:
        bot_reply = "Hey, I'm Nuru👩‍💻, your AI travel assistant. How can I help?"
    
    print(f"🤖 [Response Before Emotion] {bot_reply}")
    bot_reply = add_emotion(bot_reply, incoming_msg)
    
    if detected_language != "en":
        bot_reply = translate_text(bot_reply, detected_language)

    print(f"📤 [Final Response] Sending to user: {bot_reply}\n")

    twilio_response = MessagingResponse()
    twilio_response.message(bot_reply)
    return str(twilio_response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
