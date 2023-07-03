from PIL.Image import Image
from my_project.dither import dither as dither_effect
from PIL import ImageColor

def dither_processor(image, dither=False, inverse=False, **kwargs):
    """
    Applies an effect on the source image.
    """
    if dither:
        color = ImageColor.getrgb(dither)
        image = dither_effect(image, color=color, inverse=inverse)

    else:
        pass

    return image
