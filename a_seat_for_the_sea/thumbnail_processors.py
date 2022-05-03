from PIL.Image import Image
from a_seat_for_the_sea.dither import dither as dither_effect
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
