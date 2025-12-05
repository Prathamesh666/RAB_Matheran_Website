# iterate over all images in GALLERY_CATEGORIES to create thumbs
from PIL import Image
import os
from app import GALLERY_CATEGORIES  # or import from a shared module

SRC = "static/images"
DST = os.path.join(SRC, "thumbs")
os.makedirs(DST, exist_ok=True)
sizes = (420, 300)

for cat in GALLERY_CATEGORIES.values():
    for fname in cat["images"]:
        src_path = os.path.join(SRC, fname)
        dst_path = os.path.join(DST, fname)
        if not os.path.exists(src_path):
            print("Missing:", src_path)
            continue
        try:
            with Image.open(src_path) as im:
                im.thumbnail(sizes)
                im.save(dst_path, optimize=True, quality=85)
                print("Thumb saved:", dst_path)
        except Exception as e:
            print("Failed:", fname, e)