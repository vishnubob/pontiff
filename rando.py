#!/usr/bin/env python

import svgwrite
import random
import math
from text import *

def get_drawing(svgfn, size=(10, 10), dpi=96):
    x_res = dpi * size[0]
    y_res = dpi * size[1]
    viewbox = (0, 0, x_res, y_res)
    viewbox = str.join(' ', map(str, viewbox))
    size_x = "%sin" % size[0]
    size_y = "%sin" % size[1]
    size = (size_x, size_y)
    dwg = svgwrite.Drawing(svgfn, size=size, viewBox=viewbox, debug=False, profile="full")
    return dwg

def random_char(fontfn, alphabet):
    ftsize = random.randint(10, 100)
    ft = Font(fontfn, size=ftsize)
    x = random.randint(1, 600)
    y = random.randint(1, 600)
    angle = random.random() * (2 * math.pi)
    ft.set_transform(angle)
    ch = random.choice(alphabet)
    path = ft.get_path(ch=ch, x=x, y=y)
    return path

fontfn = "OpenSans-Regular.ttf"
alphabet = [chr(val) for val in range(33, 127)]

canvas = get_drawing("random.svg")
style = "fill:none;stroke:black;stroke-width:.5"
for x in range(100):
    path = random_char(fontfn, alphabet)
    path = canvas.path(d=path, style=style)
    canvas.add(path)
canvas.save()
