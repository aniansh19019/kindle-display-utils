import os
import argparse
from kindle_display import display_image, keep_alive

def parse_arguments():
    parser = argparse.ArgumentParser(description="Stream screen to Kindle display")
    parser.add_argument("--server", default="root@192.168.15.244", help="Server name (default: root@192.168.15.244)")
    parser.add_argument("--rotation", type=int, default=1, choices=[0, 1, 2, 3], help="Rotation (0, 1, 2, or 3, default: 1)")
    parser.add_argument("--crop", type=bool, default=False, help="Whether to crop the image (default: False)")
    parser.add_argument("--display", type=int, default=1, help="Display number to capture (default: 1)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    OUTPUT_FILENAME = "screen.png"

    # Keep the display alive
    keep_alive(True)

    try:
        while True:
            os.system(f"screencapture -x -D {args.display} -r {OUTPUT_FILENAME}")
            display_image(OUTPUT_FILENAME, args.server, rotation=args.rotation, force_refresh=False, negative=False, crop=args.crop)
            os.remove(OUTPUT_FILENAME)
    except KeyboardInterrupt:
        print("Screen streaming stopped.")
    finally:
        # Disable the display keep-alive
        keep_alive(False)

if __name__ == "__main__":
    main()
