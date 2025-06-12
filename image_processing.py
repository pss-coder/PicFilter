import io
import time
from pathlib import Path
from argparse import ArgumentParser
import uuid

from PIL import Image, ImageFilter


def light_processing(image):
    image = image.filter(ImageFilter.BLUR)
    time.sleep(1)
    return image


def heavy_processing(image):
    image = image.filter(ImageFilter.CONTOUR)
    time.sleep(60)  ## To simulate a long processing time
    return image


def main(image_data, light=False, heavy=False) -> Path:
    image = Image.open(io.BytesIO(image_data))
    if light:
        image = light_processing(image)
    if heavy:
        image = heavy_processing(image)
        
    new_path = Path(f"processed_image_{uuid.uuid4()}_{int(time.time())}.png")
    image.save(new_path)
    return new_path


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("image_path", type=Path)
    parser.add_argument("--light", action="store_true")
    parser.add_argument("--heavy", action="store_true")
    args = parser.parse_args()
    main(args.image_path, args.light, args.heavy)
