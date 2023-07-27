import requests

# Set the token value
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiI1OWI2N2I2YS1lNWYwLTQ1MzYtOTVmMy1hMzY3ZmY2OWVkODUiLCJpc3MiOiJodHRwczovL2xvZ2luLm1pY3Jvc29mdG9ubGluZS5jb20vNWUyYTNjYmQtMWE1Mi00NWFkLWI1MTQtYWI0Mjk1NmIzNzJjL3YyLjAiLCJpYXQiOjE2OTA0MjYzODgsIm5iZiI6MTY5MDQyNjM4OCwiZXhwIjoxNjkwNDMxNjIxLCJhaW8iOiJBV1FBbS84VUFBQUFWN091eG5sNkdZSWlLUVJJZGk0THFyRXYxa1J6eGd0NnlCelk5Mk9oZGNENjFweCtFNVYya2JRTkhLWEV4am1ka2NwTXhtemFabmJMYjhTSjlvQVN6bXgycWhPc0xBZVRqUzlZYUdkdnQwRzlkVzk5MUo5eTRBWE9pdkx1MjVtRyIsImF6cCI6Ijc2ZWE5MmQ2LTMzMDgtNDBkNS04NjRhLWIyN2ZiOGY1YjI3MyIsImF6cGFjciI6IjAiLCJuYW1lIjoiVGhpZW4gVHJhbiIsIm9pZCI6ImY1MjdhZGI1LWM5OGMtNDg4NS1iYjY3LThkMTc4NTI2ZDI1NCIsInByZWZlcnJlZF91c2VybmFtZSI6InRoaWVuLnRyYW5Abm9pcy52biIsInJoIjoiMC5BVWtBdlR3cVhsSWFyVVcxRkt0Q2xXczNMR3A3dGxudzVUWkZsZk9qWl85cDdZVkpBSE0uIiwicm9sZXMiOlsiVXNlciJdLCJzY3AiOiJhY2Nlc3NfYXNfdXNlciIsInN1YiI6Ik1oTGgzVnBVU2V1VE1FN2xlcjZ6Vk9VSno0Qkx6c3J0S2I4NTh3R1owMUkiLCJ0aWQiOiI1ZTJhM2NiZC0xYTUyLTQ1YWQtYjUxNC1hYjQyOTU2YjM3MmMiLCJ1dGkiOiJvYmJxakFCRk5FU04wUTVaWVNzREFBIiwidmVyIjoiMi4wIn0.HGdCskhOnIIRjRYQWckhSAB8jS-DCdHXxOopHFc49ZGpUtFe-7e5NJ4wPh0ZckmdMZTlO-Kt4H6b_2ZMULt_GswcnY78Fdh698JLnTOa4DMBKQuWpR1l_JxsJ2MKai6b8c3P-hZHI1irNohfLUs-i1fAbFt09-yw-lWLcZB68hYcHTbCd39iE_SyTJjnOp81ZkSpM-FLQMZGkR2cenwaMwJz-ZrgRQp3229-WO08UzaCxXOAVSZ0uVYrLXWoa_twYfbiNz6Xu61c5YOrL733xkCn6qa5wJqIwW1hg_2AJklJ0pYLNTai041-ajcNPLYPVsDaEgtDcpJwtjA0rkR6Ew"

# Set the request URL
url = "https://api-hrm.nois.vn/api/leaveapplication"

# Set the JSON data to include in the request body
data = {
    "reviewUserId": 139,
    "relatedUserId": "",
    "fromDate": "07/29/2023",
    "toDate": "07/30/2023",
    "leaveApplicationTypeId": 2,
    "leaveApplicationNote": "test",
    "numberOffDay": 2
}

# Set the headers to include the token
headers = {
    "Authorization": f"Bearer {token}"
}

# Make the request
response = requests.post(url, json=data, headers=headers)

# Print the response status code and content
print(response.status_code)
print(response.content)