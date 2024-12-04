
from PIL import Image, ImageFont, ImageDraw
import argparse
import numpy as np


X_RES = 1072
Y_RES = 1448

def need_rotation(input_path: str) -> bool:
    with Image.open(input_path) as img:
        width, height = img.size
        if width > height:
            return True
        else:
            return False

from PIL import Image, ImageDraw, ImageFont

def add_banner(img, title, subtitle):
    # Define banner dimensions
    box_height = 100
    box_width = img.width
    
     # Create an oval gradient banner for grayscale
    banner = Image.new('L', (box_width, box_height), 0)  # Black background
    gradient = np.zeros((box_height, box_width), dtype=np.uint8)
    center_x, center_y = box_width // 2, box_height // 2
    max_radius_x = box_width / 2  # Horizontal scaling
    max_radius_y = box_height / 2  # Vertical scaling

    for y in range(box_height):
        for x in range(box_width):
            dx = (x - center_x) / max_radius_x
            dy = (y - center_y) / max_radius_y
            distance = np.sqrt(dx**2 + dy**2)
            brightness = max(0, 1 - distance)  # Brightest at center
            gradient[y, x] = int(brightness * 70)
    
    banner = Image.fromarray(gradient, mode='L')

    # Add title and subtitle
    draw = ImageDraw.Draw(banner)
    title_font = ImageFont.truetype('futura.ttf', 30)  # Default font
    subtitle_font = ImageFont.truetype('futura.ttf', 20)  # Default font

    # Calculate title position
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (box_width - title_width) // 2
    title_y = 10  # Padding from the top
    
    # Calculate subtitle position
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (box_width - subtitle_width) // 2
    subtitle_y = title_y + 40  # Spacing below the title
    
    # Draw text in white
    draw.text((title_x, title_y), title, font=title_font, fill=255)  # White text
    draw.text((subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill=255)
    
    # Combine the original grayscale image with the banner
    new_img = Image.new('L', (img.width, img.height + box_height), 0)  # Grayscale image
    new_img.paste(img, (0, 0))
    new_img.paste(banner, (0, img.height-100))
    
    return new_img

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





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and output a grayscale png for Kindle display.")
    parser.add_argument("input_image", help="Path to the input image file")
    parser.add_argument("-o", "--output", default="output.png", help="Path to the output image file (default: output.png)")
    parser.add_argument("-c", "--crop", action="store_true", help="Crop the image to fill the screen instead of fitting to screen")
    parser.add_argument("-r", "--rotate", type=int, choices=[0, 1, 2, 3], default=0, help="Rotate the image (0: no rotation, 1: 90 degrees CW, 2: 180 degrees, 3: 270 degrees CW)")
    
    args = parser.parse_args()

    # Process the image for the kindle display
    img = process_image(args.input_image, args.crop, args.rotate)

    # Save the processed image
    img.save(args.output, 'PNG')
