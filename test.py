import requests

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiI1OWI2N2I2YS1lNWYwLTQ1MzYtOTVmMy1hMzY3ZmY2OWVkODUiLCJpc3MiOiJodHRwczovL2xvZ2luLm1pY3Jvc29mdG9ubGluZS5jb20vNWUyYTNjYmQtMWE1Mi00NWFkLWI1MTQtYWI0Mjk1NmIzNzJjL3YyLjAiLCJpYXQiOjE2OTE0NjQwMzUsIm5iZiI6MTY5MTQ2NDAzNSwiZXhwIjoxNjkxNDY5MzM0LCJhaW8iOiJBV1FBbS84VUFBQUFvSE9lZTQyL2trdHRDbnQwWkdsdU9HWTh6K1FCM0FDZzFhSlRkOGhxdGlvczZ4aHltZ2t0MmpPNEpTQVplMEhGTWlMZVpnWmxrNWw2cWU5TGh0cVhTajMvVDV6UDJvYWZuTEZBeHAxNDZOZlpVQks0RDM4QTl1bkJQajhoSC9LLyIsImF6cCI6Ijc2ZWE5MmQ2LTMzMDgtNDBkNS04NjRhLWIyN2ZiOGY1YjI3MyIsImF6cGFjciI6IjAiLCJuYW1lIjoiQnVpIEtoYW5oIiwib2lkIjoiYzEyMjM2NzgtZTA4Yy00MTE0LWFjYzAtMDg0YTUxZGQ0ZmFmIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYnVpLmtoYW5oQG5vaXMudm4iLCJyaCI6IjAuQVVrQXZUd3FYbElhclVXMUZLdENsV3MzTEdwN3Rsbnc1VFpGbGZPalpfOXA3WVZKQU9NLiIsInJvbGVzIjpbIlVzZXIiXSwic2NwIjoiYWNjZXNzX2FzX3VzZXIiLCJzdWIiOiJzX094akE0NGM4RmNERXlGMFF5TVRiN09rUGpaY2dtcmpNeXB6VVV0czlVIiwidGlkIjoiNWUyYTNjYmQtMWE1Mi00NWFkLWI1MTQtYWI0Mjk1NmIzNzJjIiwidXRpIjoiT3I4NU51dzQyRVM0ZVBrLWZFZUxBQSIsInZlciI6IjIuMCJ9.TsfhEic2DqAXnCligdcu-HWisimpAJ9_DOBCSaTyexrHM33McPlAiCKOdGOWsksdtUf0iiztg9Rie0-_iw4hj5BF0WBqBApJzEEJkO2T40E6UT7F0ZvE1JxdXEWx9guf43FznwCkCzeriklDLN9V9nQ10SddW4h-yVv8beY89h0I4pd6XrisxPOsY4dVcIzZfG2TorQ-z3Ztr0IGPwzKmpjs9u8hMkSUtQNQCaaNGYlTcB3WeB0YPWoV9Gh38B3kOiUddLQRTFBCWE9nDK89GZx8Jox-InRDU15VJRI1Jpf67iaKUQ3c8MrNCBKBZiwP6YhhTqAjH54TymZ6RdOXNg"

header = header = {"Authorization": f"Bearer {token}"}

url = "https://api-hrm.nois.vn/api/user/dayoff-data"

def get_leave_application():

  global header

  response = requests.get(url, headers=header)

  temp_list = []

  if response.status_code == 200:


      return response.json()['data']

 

  else:

      return "not successful return get_leave_application"

 

 

print(str(get_leave_application()))