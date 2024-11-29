# Kindle Display and Screen Streaming

This project allows you to display images and stream your computer screen to a Kindle device. It consists of two main Python scripts that work together to process images and send them to the Kindle for display.

## Features

- Display images on a Kindle device
- Stream your computer screen to the Kindle in real-time
- Image processing capabilities:
  - Rotation
  - Cropping
  - Fitting to screen
  - Negative display
- Keep the Kindle display alive during streaming

## Scripts

### 1. kindle_display.py

This script handles the core functionality of processing and displaying images on the Kindle.

Key features:
- Process images to fit the Kindle's display resolution (1072x1448)
- Rotate, crop, or fit images as needed
- Convert images to grayscale
- Transfer processed images to the Kindle using SCP
- Display images on the Kindle using the `eips` command

Usage:
```
python kindle_display.py input_image ssh_server [options]
```

Options:
- `-c, --crop`: Crop the image to fill the screen
- `-n, --negative`: Display the image with negative colors
- `-f, --force-refresh`: Force a refresh of the display
- `-r, --rotate {0,1,2,3}`: Rotate the image (0: no rotation, 1: 90° CW, 2: 180°, 3: 270° CW)

### 2. screen_stream.py

This script captures your computer screen and streams it to the Kindle display.

Key features:
- Capture screen using the `screencapture` command
- Continuously send screen captures to the Kindle
- Configurable server address, rotation, cropping, and display number

Usage:
```
python screen_stream.py [options]
```

Options:
- `--server`: Server name (default: root@192.168.15.244)
- `--rotation {0,1,2,3}`: Rotation (0, 1, 2, or 3, default: 1)
- `--crop`: Whether to crop the image (default: False)
- `--display`: Display number to capture (default: 1)

## Requirements

- Python 3
- Pillow (PIL) library
- SSH access to your Kindle device
- `screencapture` command (for screen streaming, typically available on macOS)

## Setup

1. Ensure you have SSH access to your Kindle device.
2. Install the required Python libraries:
   ```
   pip install pillow
   ```
3. Configure your Kindle's IP address in the scripts or use the command-line options to specify it.

## Usage

1. To display a single image:
   ```
   python kindle_display.py path/to/image.jpg root@kindle_ip_address
   ```

2. To start screen streaming:
   ```
   python screen_stream.py
   ```
   You can customize the streaming options, for example:
   ```
   python screen_stream.py --server root@192.168.1.100 --rotation 2 --crop True --display 2
   ```

Note: You can stop the screen streaming by pressing Ctrl+C.

## Troubleshooting

- Ensure your Kindle is on the same network as your computer.
- Verify that SSH access to your Kindle is properly set up.
- Check that the Kindle's IP address is correct in your commands or script configurations.

## Disclaimer

This project is for personal use and experimentation. Be cautious when using it, as it involves modifying your Kindle's display behavior. Use at your own risk.
