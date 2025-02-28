import cohere

# Initialize Cohere
cohere_client = cohere.Client("A1tvQQRVN0JQEJBr2lHY4dQOuSgwiN8AmkJnglZB")

def generate_ai_response(user_query):
    """Generates structured travel responses with 5 real examples."""
    response = cohere_client.generate(
        model="command",
        prompt=f"""
        You are a travel assistant. Provide a structured response listing 5 real-world examples related to "{user_query}". 
        Each example should include:
        - Name
        - Location
        - A short description
        - Price range (if applicable)
        - Rating (if applicable)

        Keep the response clear and structured for easy reading.
        """,
        max_tokens=300,
        temperature=0.8,  # Adjust for creativity
    )
    return response.generations[0].text.strip()

