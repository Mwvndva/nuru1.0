import cohere

# Initialize Cohere
COHERE_API_KEY = "A1tvQQRVN0JQEJBr2lHY4dQOuSgwiN8AmkJnglZB"  # Replace with your actual API key
co = cohere.Client(COHERE_API_KEY)

def generate_ai_response(user_query):
    """Generate a human-like response using Cohere AI when the database has no answer."""
    response = co.generate(
        model="command",  # You can use 'command' or 'command-light' for faster responses
        prompt=f"You are a travel assistant. Answer this user query in a friendly and helpful way:\n\n{user_query}",
        max_tokens=100,
        temperature=0.8  # Adjust for more or less creativity
    )
    return response.generations[0].text.strip()
