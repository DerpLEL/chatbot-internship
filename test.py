import requests

token = ""
header = header = {"Authorization": f"Bearer {token}"}

url_user = "https://api-hrm.nois.vn/api/user/me"
url_day_off = "https://api-hrm.nois.vn/api/chatbot/dayoff?email=bui.khanh@nois.vn"

email =""
def get_user_email():
    """
    Input: None
            
            
    Output: 
        response: user's data as dictionary
    Purpose: return user's data as dictionary
    """            
    response = requests.get(url_user, headers=header)  
    return response.json()['data']['email']

def get_day_off_user(response):
    header = {
    "api-key": "2NFGmIbGKlPkedZ25Mo9vQyM0CKSmABieUk-SCGzm9A"
    }
    url_day_off = "https://api-hrm.nois.vn/api/chatbot/dayoff?email=" + response['email']

    response = requests.get(url_day_off, headers=header)


    if response.status_code == 200:
        return response.json()['data']
    else:
        return "get error"

 
print(str(get_day_off_user()))
 

# print(str(get_leave_application()))
