from twilio.rest import Client

# Twilio credentials
TWILIO_ACCOUNT_SID = "AC3925891c3f16caca12c0078209d0f21d"
TWILIO_AUTH_TOKEN = "fc6eb3cd1a0e505827e5d296475d1013"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio sandbox number
YOUR_WHATSAPP_NUMBER = "whatsapp:+254111548797"  # Your phone number

def send_whatsapp_message(message):
    """Sends a message via WhatsApp using Twilio."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=YOUR_WHATSAPP_NUMBER
    )

    print(f"Message sent! SID: {message.sid}")

def send_message_in_chunks(response):
    """Splits long messages into chunks and sends them sequentially."""
    max_length = 1600  # Twilio message limit
    chunks = [response[i:i+max_length] for i in range(0, len(response), max_length)]
    
    for chunk in chunks:
        send_whatsapp_message(chunk)  # Send each chunk separately

# Test sending a long message with chunking
long_message = "This is a long message that exceeds Twilio's 1600-character limit. " * 50  # Simulating a long response
send_message_in_chunks(long_message)
