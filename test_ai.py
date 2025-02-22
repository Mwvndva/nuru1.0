from db_queries import get_response

location = "Nairobi"
category = "Accommodation"
subcategory = "Hotels"

response = get_response(location, category, subcategory)
print(response)
