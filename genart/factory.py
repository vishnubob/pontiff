#!/usr/bin/env python

import svgwrite
import math
import StringIO
import pylru
import PIL
import numpy
from . text import *

__all__ = ["FaceFactory"]

class FaceFactory(object):
    def __init__(self, font_filename, size, target_size=None):
        self.font_filename = font_filename
        self.size = size
        self.path_cache = pylru.lrucache(10000)
        self.bitmap_cache = pylru.lrucache(10000)
        self.target_size = target_size if target_size != None else size
        self.alphabet = [chr(val) for val in range(33, 127)]
        self.rules = (
            ("ch", len(self.alphabet) - 1, lambda i: self.alphabet[int(round(i))]),
            ("x", self.size[0], float),
            ("y", self.size[1], float),
            ("angle", 2 * math.pi, float),
            ("size", (self.size[0] * self.size[1]) ** .5 / 32.0, float),
        )

    def builder(self, state):
        ptr = iter(state)
        while 1:
            try:
                yield self.build_individual(ptr)
            except StopIteration:
                break

    def build_individual(self, ptr):
        kw = [("fontfile", self.font_filename)]
        for (attr, maxval, castfun) in self.rules:
            val = castfun(ptr.next() * maxval)
            kw.append((attr, val))
        return tuple(kw)

    def get_canvas(self, svgfn):
        x_res = self.size[0]
        y_res = self.size[1]
        viewbox = (0, 0, x_res, y_res)
        viewbox = str.join(' ', map(str, viewbox))
        size_x = str(self.target_size[0])
        size_y = str(self.target_size[1])
        size = (size_x, size_y)
        dwg = svgwrite.Drawing(svgfn, size=size, viewBox=viewbox, debug=False, profile="full")
        return dwg

    def render(self, state, svgfn=''):
        style = "fill:none;stroke:black;stroke-width:.5"
        canvas = self.get_canvas(svgfn)
        for facekw in self.builder(state):
            if facekw not in self.path_cache:
                face = Font(**dict(facekw))
                path = face.get_path(yoff=self.size[1])
                self.path_cache[facekw] = path
            path = self.path_cache[facekw]
            path = canvas.path(d=path, style=style)
            canvas.add(path)
        if not svgfn:
            buf = StringIO.StringIO()
            canvas.write(buf)
            return buf.getvalue()
        else:
            canvas.save()
            return svgfn

    def render_bitmap(self, state):
        img = PIL.Image.new('L', self.size, color=0xff)
        for facekw in self.builder(state):
            if facekw not in self.bitmap_cache:
                face = Font(**dict(facekw))
                res = face.get_bitmap()
                (top, left, width, rows, pitch, bitmap) = res
                inv_bitmap = [0xff - val for val in bitmap]
                bitmap_str = str.join('', map(chr, inv_bitmap))
                mask_str = str.join('', map(chr, bitmap))
                fimg = PIL.Image.frombytes('L', (width, rows), bitmap_str)
                mask = PIL.Image.frombytes('L', (width, rows), mask_str)
                self.bitmap_cache[facekw] = (fimg, mask, (left, self.size[1] - top))
            (bitmap, mask, anchor) = self.bitmap_cache[facekw]
            img.paste(bitmap, anchor, mask=mask)
        return numpy.array(img)
