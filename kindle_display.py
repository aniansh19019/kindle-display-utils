from PIL import Image
import os
import subprocess
import argparse
import time

X_RES = 1072
Y_RES = 1448
DISPLAY_COMMAND = "eips -g {}" 
OUTPUT_FILENAME = "display.png"
DISPLAY_KEEPALIVE_ENABLE_COMMAND = "lipc-set-prop com.lab126.powerd preventScreenSaver 1"
DISPLAY_KEEPALIVE_DISABLE_COMMAND = "lipc-set-prop com.lab126.powerd preventScreenSaver 0"
BACKLIGHT_OBJECT = "/sys/devices/platform/imx-i2c.0/i2c-0/0-003c/max77696-bl.0/backlight/max77696-bl/brightness"
ACTUAL_BRIGHTNESS_OBJECT = "/sys/devices/platform/imx-i2c.0/i2c-0/0-003c/max77696-bl.0/backlight/max77696-bl/actual_brightness"
BACKLIGHT_DRIVER = "/sys/devices/platform/imx-i2c.0/i2c-0/0-003c/max77696-bl.0/driver/"
BACKLIGHT_NAME = "max77696-bl.0"


def backlight_hotfix(server):
    bind_command = "echo -n " + BACKLIGHT_NAME + " > " + BACKLIGHT_DRIVER + "bind"
    unbind_command = "echo -n " + BACKLIGHT_NAME + " > " + BACKLIGHT_DRIVER + "unbind"
    subprocess.run("ssh " + server + " " + '"' + bind_command + '"', shell=True, check=True)
    subprocess.run("ssh " + server + " " + '"' + unbind_command + '"', shell=True, check=True)


def set_backlight(val, server):
    # val should be between 0 and 4095
    if val < 0:
        val = 0
    elif val > 4095:
        val = 4095
    subprocess.run("ssh " + server + ' "'+ " echo " + str(val) + " > " + BACKLIGHT_OBJECT + '"', shell=True, check=True)
    if get_actual_backlight(server) != val:
        backlight_hotfix(server)

def get_actual_backlight(server):
    return int(subprocess.run("ssh " + server + ' "'+ " cat " + ACTUAL_BRIGHTNESS_OBJECT + '"', shell=True, check=True, capture_output=True).stdout.decode("utf-8"))

def get_backlight(server):
    return int(subprocess.run("ssh " + server + ' "'+ " cat " + BACKLIGHT_OBJECT + '"', shell=True, check=True, capture_output=True).stdout.decode("utf-8"))

def keep_alive(enable, server):
    if enable:
        subprocess.run("ssh " + server + " "  + ' "'+ DISPLAY_KEEPALIVE_ENABLE_COMMAND + '"', shell=True, check=True)
    else:
        subprocess.run("ssh " + server + " " + ' "'+ DISPLAY_KEEPALIVE_DISABLE_COMMAND + '"', shell=True, check=True)


def process_image(input_path, crop=False, rotation=0):
    with Image.open(input_path) as img:
        # Rotate image if needed
        if rotation:
            img = img.rotate(rotation * 90, expand=True)

        # Get original image size
        orig_width, orig_height = img.size

        # Calculate aspect ratios
        target_ratio = X_RES / Y_RES
        img_ratio = orig_width / orig_height

        if crop:
            # Crop to screen (fill entire screen, centered crop)
            if img_ratio > target_ratio:
                # Image is wider, scale to match height
                new_height = Y_RES
                new_width = int(new_height * img_ratio)
            else:
                # Image is taller, scale to match width
                new_width = X_RES
                new_height = int(new_width / img_ratio)

            # Resize the image
            img = img.resize((new_width, new_height), Image.LANCZOS)

            # Calculate the crop box
            left = (new_width - X_RES) // 2
            top = (new_height - Y_RES) // 2
            right = left + X_RES
            bottom = top + Y_RES

            # Crop the image
            img = img.crop((left, top, right, bottom))
        else:
            # Fit to screen (maintain aspect ratio, no cropping)
            if img_ratio > target_ratio:
                # Image is wider, scale to match width
                new_width = X_RES
                new_height = int(X_RES / img_ratio)
            else:
                # Image is taller, scale to match height
                new_height = Y_RES
                new_width = int(Y_RES * img_ratio)

            # Resize the image
            img = img.resize((new_width, new_height), Image.LANCZOS)

        # Create a black background
        background = Image.new('RGB', (X_RES, Y_RES), (0, 0, 0))

        # Paste the processed image onto the center of the black background
        offset = ((X_RES - img.width) // 2, (Y_RES - img.height) // 2)
        background.paste(img, offset)
        img = background

        

        # convert to grayscale
        img = img.convert('L')

        # Return the processed image
        return img


def display_image(input_path, ssh_server, crop=False, rotation=0, negative=False, force_refresh=True):
    # Process the image for the kindle display
    img = process_image(input_path, crop, rotation)

    # Save the processed image
    img.save(OUTPUT_FILENAME, 'PNG')

    # SCP the image to the Kindle
    scp_command = f"scp {OUTPUT_FILENAME} {ssh_server}:~/{OUTPUT_FILENAME}"
    subprocess.run(scp_command, shell=True, check=True)

    # SSH into the Kindle and run the display command
    ssh_command = f"ssh {ssh_server} '{DISPLAY_COMMAND.format(OUTPUT_FILENAME + (" -v" if negative else "") + (" -f" if force_refresh else ""))}'"
    subprocess.run(ssh_command, shell=True, check=True)

    # Clean up the local processed image
    os.remove(OUTPUT_FILENAME)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and display an image on Kindle.")
    parser.add_argument("input_image", help="Path to the input image file")
    parser.add_argument("ssh_server", help="SSH server address (e.g., root@192.168.0.1)")
    parser.add_argument("-c", "--crop", action="store_true", help="Crop the image to fill the screen instead of fitting to screen")
    parser.add_argument("-n", "--negative", action="store_true", help="Display the image with negative colors")
    parser.add_argument("-f", "--force-refresh", action="store_true", help="Force a refresh of the display")
    parser.add_argument("-a", "--keep-alive", action="store_true", help="Keep the display alive after displaying the image")
    parser.add_argument("-r", "--rotate", type=int, choices=[0, 1, 2, 3], default=0, help="Rotate the image (0: no rotation, 1: 90 degrees CW, 2: 180 degrees, 3: 270 degrees CW)")
    # argument for bnacklight, values from 0 to 4095
    parser.add_argument("-b", "--backlight", type=int, default=-1, help="Set the backlight brightness (0 to 4095)")
    

    args = parser.parse_args()

    if args.backlight != -1:
        set_backlight(args.backlight, args.ssh_server)

    # SSH into the Kindle and run the keep-alive command
    if args.keep_alive:
        keep_alive(True, args.ssh_server)
    else:
        keep_alive(False, args.ssh_server)
    
    # backlight = get_actual_backlight(args.ssh_server)
    # set_backlight(4095, args.ssh_server)
    display_image(args.input_image, args.ssh_server, args.crop, args.rotate, args.negative)
    

    print(f"Image processed, transferred, and displayed on Kindle at {args.ssh_server}")
    # time.sleep(5)
    # set_backlight(backlight, args.ssh_server)
