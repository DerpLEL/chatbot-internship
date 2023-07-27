import msal

# Set up the MSAL client with your client ID and authority URL
client_id = "d70aeb25-d473-4545-b414-70e9050580bf"
authority_url = "https://login.microsoftonline.com/5e2a3cbd-1a52-45ad-b514-ab42956b372c"
app = msal.PublicClientApplication(client_id, authority=authority_url)

# Define the scopes that you want to request access to
scopes = ["User.Read"]

# Send a login request to the Microsoft authentication service
result = app.acquire_token_interactive(scopes=scopes)

# Extract the token from the result object


# Print the token to the console
print("Your authentication token is:", result)