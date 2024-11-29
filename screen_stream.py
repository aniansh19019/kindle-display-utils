import os
import argparse
from kindle_display import display_image, keep_alive, set_backlight, get_actual_backlight

def parse_arguments():
    parser = argparse.ArgumentParser(description="Stream screen to Kindle display")
    parser.add_argument("-s", "--server", default="root@192.168.15.244", help="Server name (default: root@192.168.15.244)")
    parser.add_argument("-r", "--rotation", type=int, default=1, choices=[0, 1, 2, 3], help="Rotation (0, 1, 2, or 3, default: 1)")
    parser.add_argument("-c", "--crop", action="store_true", help="Whether to crop the image (default: False)")
    parser.add_argument("-d", "--display", type=int, default=1, help="Display number to capture (default: 1)")
    parser.add_argument("-b", "--backlight", type=int, default=-1, help="Set the backlight brightness (0 to 4095)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    OUTPUT_FILENAME = "screen.png"
    FORCE_REFRESH_INTERVAL = 10

    # Keep the display alive
    keep_alive(True, args.server)

    # Get the actual backlight brightness
    backlight = get_actual_backlight(args.server)
    # Set the backlight brightness
    if args.backlight != -1:
        set_backlight(args.backlight, args.server)

    counter = 0
    try:
        while True:
            os.system(f"screencapture -x -D {args.display} -r {OUTPUT_FILENAME}")
            if counter%FORCE_REFRESH_INTERVAL == 0:
                display_image(OUTPUT_FILENAME, args.server, rotation=args.rotation, force_refresh=True, negative=False, crop=args.crop)
            else:
                display_image(OUTPUT_FILENAME, args.server, rotation=args.rotation, force_refresh=False, negative=False, crop=args.crop)
            os.remove(OUTPUT_FILENAME)
            counter += 1
            
    except KeyboardInterrupt:
        print("Screen streaming stopped.")
    finally:
        # Disable the display keep-alive
        keep_alive(False, args.server)
        # Set the backlight brightness back to its original value
        set_backlight(backlight, args.server)

if __name__ == "__main__":
    main()
