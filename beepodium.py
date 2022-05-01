from PIL import Image, ImageDraw
import requests
import io 

def open_img_from_url(url):
    response = requests.get(url)
    image_bytes = io.BytesIO(response.content)
    img = Image.open(image_bytes).resize((300, 300))
    return img

def get_profile_mask(size):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    return mask

def put_place(podium, user, place:int):
    if place == 1:
        pos = (860, 200)
    elif place == 2:
        pos = (400,300)
    elif place == 3:
        pos = (1330,350)
    x,y = pos

    img = open_img_from_url(user['avatar'])
    podium.paste(img, (x,y), get_profile_mask(img.size))

def create_podium(user1, user2=None, user3=None):
    imgPodium = Image.open("img/podio.jpg")

    put_place(imgPodium, user1, 1)
    if user2: put_place(imgPodium, user2, 2)
    if user3: put_place(imgPodium, user3, 3)

    bio = io.BytesIO()
    bio.name = 'podio_tmp.jpeg'
    imgPodium.save(bio, 'JPEG')
    bio.seek(0)

    return bio

