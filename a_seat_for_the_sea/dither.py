#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageOps
import re


def color (color):
    if type(color) is str:
        m = re.match(r'(\d+),\s*(\d+),\s*(\d+)', color)

        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        else:
            return (0,0,0)
    else:
       return color


def dither(image, threshold=125, color=(0,0,0,255), scale=1, postscale=1, colormap=None, inverse=False):

    im = image.convert('1', colors=2)

    # im = im.resize((int(im.size[0] * scale), int(im.size[1] * scale)), Image.BICUBIC)

    # if inverse:
    #     im = ImageOps.invert(im)

    # if colormap:
    #     im_out = colormap.resize((im.size[0], im.size[1]), Image.BICUBIC).convert('RGBA')
    # else:
    #     im_out = Image.new(mode='RGBA', size=(im.size[0], im.size[1]), color=color)


    # px_in = im.load()
    # px_out = im_out.load()

    # neighbours = ((1,0), (2,0), (-1,1), (0,1), (1,1), (0,2))

    # for y in range(im.size[1]):
    #     for x in range(im.size[0]):
    #         old = px_in[x, y]
    #         new = 255 if old > threshold else 0
    #         err = (old - new) >> 3

    #         if new == 255:
    #             px_out[x,y] = (color[0], color[1], color[2], 0)

    #         for c in neighbours:
    #             try:
    #                 px_in[x+c[0], y+c[1]] += err
    #             except IndexError:
    #                 pass

    # if postscale > 1:
    #     im_out = im_out.resize((im_out.size[0] * postscale, im_out.size[1] * postscale), Image.NEAREST)

    return im


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--color', dest='color', default=(0,0,0), type=color, help="Color to dither the image.\n\nIn the format of a comma-separated list \d+,\d+,\d+ Defaults to black ( 0,0,0 ).")
    parser.add_argument('-t', '--threshold', dest='threshold', default=128, type=int, help="Threshold after which a pixel is either turned on or of.")
    parser.add_argument('-s', '--scale', dest='scale', default=1.0, type=float, help="Sets the amount the source-image is scaled before dithering")
    parser.add_argument('-ps', '--post-scale', dest='postscale', default=1, type=int, help="Sets the amount of scaling performed after the dithering. Given in integers. Uses neirest neighbour for the scaling")
    parser.add_argument('-cm', '--color-map', dest='colormap', default=None, type=str, help="Take colors from given image to color the the dithering pixels")
    parser.add_argument('source', help="The location of the image to dither.")
    parser.add_argument('output', help="The location to save the resulting image.")
    args = parser.parse_args()

    im = Image.open(args.source)
    im = dither(im, threshold=args.threshold, color=args.color, scale=args.scale, postscale=args.postscale, colormap=args.colormap)
    im.save(args.output)

