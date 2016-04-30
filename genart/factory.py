#!/usr/bin/env python

import svgwrite
import math
import StringIO
import pylru
import PIL
import numpy
from . text import *
from . cache import get_cache

__all__ = ["FaceFactory"]

class FaceFactory(object):
    DEFAULT_CACHE_SIZE = 10000

    def __init__(self, font_filename, size):
        self.font_filename = font_filename
        self.size = size
        self.alphabet = [chr(val) for val in range(33, 127)]
        self.cache_size = self.DEFAULT_CACHE_SIZE
        self._init()

    def _init(self):
        self.path_cache = get_cache(self.cache_size)
        self.bitmap_cache = get_cache(self.cache_size)
        self.rules = (
            ("ch", len(self.alphabet) - 1, lambda i: self.alphabet[int(round(i))]),
            ("x", self.size[0], float),
            ("y", self.size[1], float),
            ("angle", 2 * math.pi, float),
            ("size", (self.size[0] * self.size[1]) ** .5 / 8.0, float),
        )

    def __getstate__(self):
        state = {
            "font_filename": self.font_filename,
            "size": self.size,
            "alphabet": self.alphabet,
        }
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._init()

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
        viewbox = tuple([0, 0] + list(self.size))
        viewbox = str.join(' ', map(str, viewbox))
        dwg = svgwrite.Drawing(svgfn, size=self.size, viewBox=viewbox, debug=False, profile="full")
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

    def render_bitmap(self, state, mode='L'):
        img = PIL.Image.new(mode, self.size, color=0xff)
        for facekw in self.builder(state):
            ckey = facekw + ("mode", mode)
            ckey = str(hash(ckey))
            if ckey not in self.bitmap_cache:
                face = Font(**dict(facekw))
                try:
                    res = face.get_bitmap(radius=.5)
                    (top, left, width, rows, pitch, bitmap) = res
                    inv_bitmap = [0xff - val for val in bitmap]
                    bitmap_str = str.join('', map(chr, inv_bitmap))
                    mask_str = str.join('', map(chr, bitmap))
                    fimg = PIL.Image.frombytes(mode, (width, rows), bitmap_str)
                    mask = PIL.Image.frombytes(mode, (width, rows), mask_str)
                    self.bitmap_cache[ckey] = (fimg, mask, (left, self.size[1] - top))
                except KeyboardInterrupt:
                    raise
                except:
                    self.bitmap_cache[ckey] = None
            res = self.bitmap_cache[ckey]
            if res == None:
                continue
            (bitmap, mask, anchor) = res
            img.paste(bitmap, anchor, mask=mask)
        return img
