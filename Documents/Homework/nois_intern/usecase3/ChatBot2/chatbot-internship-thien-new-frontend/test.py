from PIL import Image
import urllib.request
import io

URL = 'http://www.w3schools.com/css/trolltunga.jpg'

with urllib.request.urlopen(URL) as url:
    f = io.BytesIO(url.read())

img = Image.open(f)

# Get the size of the image
width, height = img.size
print("Image size:", width, "x", height)

img.show()