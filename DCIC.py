import io
from PIL import Image
from pillow_heif import register_heif_opener
import rawpy

# Enable HEIF/HEIC support in Pillow
register_heif_opener()

def convert_to_jpg(file_storage, ext):
    """
    Convert HEIC, TIFF, RAW formats to JPG using Pillow/pillow-heif/rawpy.
    Returns a BytesIO object with JPG data.
    """
    if ext in ['heic', 'heif']:
        # Pillow can now open HEIC directly thanks to pillow-heif
        image = Image.open(file_storage)
    elif ext in ['tiff', 'tif']:
        # Pillow handles TIFF directly
        image = Image.open(file_storage)
    elif ext in ['cr2', 'nef', 'arw', 'orf', 'rw2', 'dng']:
        # RAW formats handled via rawpy
        raw = rawpy.imread(file_storage)
        rgb = raw.postprocess()
        image = Image.fromarray(rgb)
    else:
        # Fallback for other formats
        image = Image.open(file_storage)

    # Save as JPG into memory
    output = io.BytesIO()
    image.save(output, format="JPEG")
    output.seek(0)
    return output