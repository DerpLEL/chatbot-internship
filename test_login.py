from selenium import webdriver
import webbrowser
import time

# Set up the driver for your specific browser (e.g. Edge, Chrome, Firefox)
driver = webdriver.Edge()

# Navigate to the login page
driver.get("https://hrm.nois.vn/")

# Wait for the page to load
time.sleep(2)

while driver.current_url != "https://hrm.nois.vn/ps/leave/self":
   time.sleep(2) 

if driver.current_url == "https://hrm.nois.vn/ps/leave/self":
    print("Login successful!")
else:
    print("Login failed.")

# Quit the browser
driver.quit()