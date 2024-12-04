#!/usr/bin/python3.9
from requests import get
import os
from urllib.parse import urlparse
from process_image import process_image, need_rotation, add_banner
from time import sleep
from datetime import datetime

# ! Remove date parameter

APOD_API = "https://api.nasa.gov/planetary/apod?thumbs=true&api_key=HUFa1yb9jA1C7KJtdur4cpC2Ps5WvFZEbdygm7hh"
SS_DIR = "/mnt/us/linkss/screensavers/"
SS_NAME = "bg_ss00.png"
SCRATCH_DIR = "/mnt/us/scratch_space/"
LINKSS_DIR = "/mnt/us/extensions/linkss/"
RESTART_FRAMEWORK_COMMAND = "bin/linkss.sh framework_restart"

def fetch_apod_image_url():
    image_url = None
    title = "APOD"
    date = ""
    try:
        json_data = get(APOD_API).json()
        print(json_data)
        if json_data["media_type"] == "image":
            image_url = json_data["url"]
            title = json_data['title']
            date = json_data['date']
            pass
        elif json_data["media_type"] == "video":
            image_url = json_data["thumbnail_url"]
            title = json_data['title']
            date = json_data['date']
            pass
        else:
            print("Invalid media type")
            return None

    except Exception as e:
        print(f"Error fetching APOD data: {e}")
        return None
    if date != "":
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date = date_obj.strftime("%d %B %Y")
    return date, title, image_url

def get_image_filename(image_url):
    return os.path.basename(urlparse(image_url).path)

def download_image(image_url, output_path):
    # Download the image to output_path and return the downloaded image file name
    try:
        # Get the image file name from the URL
        image_filename = get_image_filename(image_url)
        output_path = os.path.join(output_path, image_filename)
        # Download the image
        response = get(image_url)
        with open(output_path, "wb") as f:
            f.write(response.content)
        return image_filename
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None
    
def restart_framework():
    try:
        os.chdir(LINKSS_DIR)
        os.system(RESTART_FRAMEWORK_COMMAND)
    except Exception as e:
        print(f"Error restarting framework: {e}")

    
def empty_dir(path):
    if not os.path.isdir(path):
        print(path + " is not a directory")
        exit(-1)
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):  # Check if it's a file
            os.remove(file_path)  # Remove the file

def prep_image(img_path, title = None, subtitle = None):
    rotation = 0
    if need_rotation(img_path):
        rotation = 1
    img = process_image(img_path, crop = True, rotation=rotation)
    if title != None and subtitle != None:
        img = add_banner(img, title, subtitle)
    return img


def main():
    # Wait for 10 seconds before starting the APOD program
    sleep(10)
    os.system('eips "APOD program was run."')
    date, title, image_url = fetch_apod_image_url()
    if image_url is None:
        print("Error fetching APOD image URL")
        exit(1)

    # Get the image filename
    image_filename = get_image_filename(image_url)
    # Check if image exists already
    if os.path.exists(os.path.join(SCRATCH_DIR, image_filename)):
        # No need to do anything since no new images are available
        exit(0)

    # If the image is not already present and we have a new image, delete all images from the scratch dir
    empty_dir(SCRATCH_DIR)
    
    # Download the image
    image_filename = download_image(image_url, SCRATCH_DIR)
    if image_filename is None:
        print("Error downloading image")
        exit(1)

    # Process the image
    img = prep_image(os.path.join(SCRATCH_DIR, image_filename), title, date)

    # Save the processed image
    img.save(os.path.join(SS_DIR, SS_NAME), 'PNG')

    # Display confirmation on kindle screen
    os.system('eips "Successfully Downloaded and Converted APOD."')


def local_test():
    # date, title, url = fetch_apod_image_url()
    # img_filename = download_image(url, '.')
    title = "This is an elaborate test of NASA APOD"
    date = "2024-12-02"
    img_filename = "0.jpg"
    banner = title + '\n' + date
    print(banner)
    img = prep_image(img_filename, title, date)
    # Save the processed image
    img.save('output.png', 'PNG')

if __name__ == "__main__":
    # main()
    local_test()

    
