from twilio.rest import Client

# Twilio credentials
TWILIO_ACCOUNT_SID = "AC97a6fa39e6803bb434f979252fab9252"
TWILIO_AUTH_TOKEN = "44caac4a2d4c57e196f8d96dcf023783"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio sandbox number
YOUR_WHATSAPP_NUMBER = "whatsapp:+254111548797"  # Your phone number

def send_whatsapp_message(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=YOUR_WHATSAPP_NUMBER
    )

    print(f"Message sent! SID: {message.sid}")

# Test sending a message
send_whatsapp_message("Hello from your AI-powered travel chatbot! 🚀")
