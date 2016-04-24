#!/usr/bin/env python

import svgwrite
import math
import StringIO
from . text import *

__all__ = ["FaceFactory"]

class FaceFactory(object):
    def __init__(self, font_filename, size, target_size=None):
        self.font_filename = font_filename
        self.size = size
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
        kw = {}
        for (attr, maxval, castfun) in self.rules:
            val = castfun(ptr.next() * maxval)
            kw[attr] = val
        kkw = {
            "pen": (kw['x'], kw['y']),
            "angle": kw["angle"],
            "size": kw["size"],
            "ch": kw["ch"],
            "fontfile": self.FontFilename,
        }
        return kkw

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
        for face in self.builder(state):
            face = Font(**face)
            path = face.get_path()
            path = canvas.path(d=path, style=style)
            canvas.add(path)
        if not svgfn:
            buf = StringIO.StringIO()
            canvas.write(buf)
            return buf.getvalue()
        else:
            canvas.save()
            return svgfn
