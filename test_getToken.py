from selenium import webdriver
import time
import requests

# Set up the driver for your specific browser (e.g. Edge, Chrome, Firefox)
driver = webdriver.Edge()

# Navigate to the website you want to capture the API requests from
driver.get("https://hrm.nois.vn/ps/leave/self")

# Wait for the page to load
time.sleep(10)

# Get all the network requests made by the website
network_requests = driver.execute_script("""
    var performance = window.performance || window.webkitPerformance || window.mozPerformance || window.msPerformance || {};
    var network = performance.getEntries() || {};
    return network;
""")

# Extract the URL field from each network request and print it if it matches an API endpoint
for request in network_requests:
    url = request['name']
    if url == 'https://api-hrm.nois.vn/api/user/me':
        print(request)
    
# Quit the browser
driver.quit()