import time
import os
from django.utils.text import slugify

def candidate_directory(instance, filename):
    """
    Generates a safe upload path for candidate images using candidate code or name.
    """
    ext = os.path.splitext(filename)[1] 
    identifier = instance.code or slugify(getattr(instance.student, 'full_name', 'candidate'))
    filename = f"{int(time.time())}_{identifier}{ext}"

    return "/".join(["images", "candidates", filename])
