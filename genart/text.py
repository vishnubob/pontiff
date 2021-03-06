from decimal import *
import math
import freetype

__all__ = ["Font"]

def FT_CURVE_TAG(flag):
    return flag & 0x3

FT_CURVE_TAG_ON = 1
FT_CURVE_TAG_CONIC = 0
FT_CURVE_TAG_CUBIC = 2

def is_curve_on(flag):
    return bool(FT_CURVE_TAG(flag) == FT_CURVE_TAG_ON)

def is_conic(flag):
    return bool(FT_CURVE_TAG(flag) == FT_CURVE_TAG_CONIC)

def is_cubic(flag):
    return bool(FT_CURVE_TAG(flag) == FT_CURVE_TAG_CUBIC)

def midpoint(pt1, pt2):
    res = []
    for (p1, p2) in zip(pt1, pt2):
        res.append((p1 + p2) / 2.0)
    return tuple(res)

def to_fixed_point(num, width):
    frac = int((2 ** width - 1) * (num % 1))
    return (int(num) << width) | frac

def from_fixed_point(num, width):
    mask = int((2 ** width - 1))
    frac = (num & mask) / float(mask)
    return (num >> width) + frac

class Font(object):
    Cache = {}

    def __init__(self, fontfile='', size=10, ch=' ', angle=0, pen=None, x=None, y=None, flags=None):
        if fontfile not in self.Cache:
            face = freetype.Face(fontfile)
            self.Cache[fontfile] = face
        self._face = self.Cache[fontfile]
        self.ch = ch 
        self.flags = flags
        self.size = size
        if pen == None:
            x = x if x != None else 0
            y = y if y != None else 0
            pen = (x, y)
        self._pen = pen
        self._angle = angle

    def set_size(self, size):
        try:
            (width, height) = size
        except TypeError:
            width = height = size
        self.width = width
        self.height = height
        self._size = (self.width, self.height)

    @property
    def rotation_matrix(self):
        matrix = freetype.FT_Matrix()
        matrix.xx = int(math.cos(self._angle) * 0x10000)
        matrix.xy = int(-math.sin(self._angle) * 0x10000)
        matrix.yx = int(math.sin(self._angle) * 0x10000)
        matrix.yy = int(math.cos(self._angle) * 0x10000)
        return matrix

    @property
    def offset(self):
        pen = freetype.FT_Vector()
        pen.x = int(self._pen[0] * 64)
        pen.y = int(self._pen[1] * 64)
        return pen
    
    @property
    def face(self):
        fixed_width = to_fixed_point(self.width, 6)
        fixed_height = to_fixed_point(self.height, 6)
        self._face.set_char_size(fixed_width, fixed_height)
        self._face.set_transform(self.rotation_matrix, self.offset)
        self._face.load_char(self.ch, flags=self.flags)
        return self._face

    def set_transform(self, angle=0, pen=(0, 0)):
        self._angle = angle
        self._pen = pen

    @property
    def glyph(self):
        return self.face.glyph

    @property
    def outline(self):
        return self.glyph.outline
    
    @property
    def bbox(self):
        bbox = self.face.bbox
        attr = ("xMin", "xMax", "yMin", "yMax")
        bbox = {key: from_fixed_point(getattr(bbox, key), 6) for key in attr}
        return bbox

    def get_contours(self):
        contours = []
        start = 0
        for contour_idx in self.outline.contours:
            end = contour_idx + 1
            content = zip(self.outline.tags[start:end], self.outline.points[start:end])
            content.reverse()
            start = end
            contours.append(Contour(content))
        return contours
        
    def get_path(self, yoff=None):
        path = []
        yoff = yoff if yoff != None else self.metrics["height"]
        for contour in self.get_contours():
            for pathcmd in contour.iter_path():
                cmd = pathcmd[0]
                points = pathcmd[1:]
                points = [Point(x=pt.x, y=yoff - pt.y, flags=pt.flags) for pt in points]
                points = str.join(' ', [str(point) for point in points])
                cmd = "%s %s" % (cmd, points)
                path.append(cmd)
        return str.join(' ', path)

    def get_bitmap(self, radius=.001):
        self.flags = freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP
        glyph = self.glyph.get_glyph()
        stroker = freetype.Stroker()
        radius = to_fixed_point(radius, 6);
        stroker.set(radius, freetype.FT_STROKER_LINECAP_ROUND, freetype.FT_STROKER_LINEJOIN_ROUND, 0)
        glyph.stroke(stroker)
        blyph = glyph.to_bitmap(freetype.FT_RENDER_MODE_NORMAL, freetype.Vector(0, 0))
        bitmap = blyph.bitmap.buffer[:]
        top, left = blyph.top, blyph.left
        width, rows, pitch = blyph.bitmap.width, blyph.bitmap.rows, blyph.bitmap.pitch
        self.flags = 0
        ret = (top, left, width, rows, pitch, bitmap)
        return ret
    
    def kern(self, prevch, nextch):
        vec = self.face.get_kerning(prevch, nextch)
        return {'x': from_fixed_point(vec.x, 6), 'y': from_fixed_point(vec.y, 6)}
    
    @property
    def char_index(self):
        return self.face.get_char_index(self.ch)

    @property
    def metrics(self):
        metrics = self.glyph.metrics
        attr = [key for key in metrics.__class__.__dict__ if not key.startswith("__")]
        metrics = {key: from_fixed_point(getattr(metrics, key), 6) for key in attr}
        return metrics

    @property
    def advance_x(self):
        return from_fixed_point(self.glyph.advance.x, 6)

    @property
    def advance_y(self):
        return from_fixed_point(self.size.height, 6)

    @property
    def descender(self):
        return from_fixed_point(self.face.descender, 6)

    def _get_size(self):
        return self._size
    def _set_size(self, size):
        self.set_size(size)
    size = property(_get_size, _set_size)

    def _get_transform(self):
        return (self._angle, self.offset)
    def _set_transform(self, angle_pen):
        self.set_transform(*angle_pen)
    transform = property(_get_transform, _set_transform)

    def _get_angle(self):
        return self._angle
    def _set_angle(self, angle):
        self.transform = (angle, self._pen)
    angle = property(_get_angle, _set_angle)

    def _get_pen(self):
        return self._pen
    def _set_pen(self, pen):
        self.transform = (self._angle, pen)
    pen = property(_get_pen, _set_pen)

class Point(object):
    def __init__(self, x, y, flags):
        self.x = x
        self.y = y
        self.flags = flags

    @property
    def is_on(self):
        return is_curve_on(self.flags)

    @property
    def is_off(self):
        return not self.is_on

    @property
    def is_cubic(self):
        return is_cubic(self.flags)
    
    @property
    def is_conic(self):
        return is_conic(self.flags)

    def midpoint(self, other):
        x = (self.x + other.x) / 2.0
        y = (self.y + other.y) / 2.0
        return self.__class__(x, y, FT_CURVE_TAG_ON)
    
    def offset(self, x=0, y=0):
        return self.__class__(self.x + x, self.y + y, self.flags)

    def __str__(self):
        return "%s %s" % (self.x, self.y)

class Contour(list):
    def __init__(self, data):
        for point in data:
            self.add_point(*point)

    def add_point(self, tag, point):
        x = from_fixed_point(point[0], 6) 
        y = from_fixed_point(point[1], 6)
        point = Point(x, y, tag)
        self.append(point)

    def iter_path(self):
        for (idx, point) in enumerate(self):
            if idx == 0:
                if point.is_on:
                    first_point = point
                elif self[-1].is_off:
                    first_point = point.midpoint(self[-1])
                else:
                    first_point = self[-1]
                yield ('M', first_point)
                continue
            prev_point = self[idx - 1] if idx > 0 else None
            if point.is_on:
                if prev_point.is_on:
                    yield ('L', point)
                elif prev_point.is_off:
                    yield ('Q', prev_point, point)
                else:
                    raise RuntimeError, "bug!"
            elif point.is_off:
                if prev_point.is_off:
                    yield ('Q', prev_point, prev_point.midpoint(point))
        if self[0].is_on:
            if self[-1].is_on:
                yield ('Z')
            elif self[-1].is_off:
                yield ('Q', self[-1], self[0])
            else:
                raise RuntimeError, "bug!"

class PathText(object):
    path_tmpl = '<path d="%s" style="fill:none;stroke:black;stroke-width:.5"/>'

    class TooSmall(Exception):
        pass

    def __init__(self, font, origin, size, kernflag=True):
        self.font = font
        self.kernflag = kernflag
        self.origin = origin
        self.size = size

    def get_width(self, text):
        last_ch = None
        x = 0
        for ch in text:
            self.font.ch = ch
            x += self.font.advance_x
            if last_ch and self.kernflag:
                kern = self.font.kern(last_ch, ch)
                x += kern['x']
            last_ch = ch
        return x

    def iter_words(self, text):
        for word in text.split(' '):
            yield word

    def path(self, pen, text):
        last_ch = None
        path = ''
        (x, y) = pen
        for ch in text:
            if last_ch and self.kernflag:
                kern = self.font.kern(last_ch, ch)
                x += kern['x']
                y += kern['y']
            last_ch = ch
            path += self.font.get_path(ch, x=x, y=y)
            x += self.font.advance_x
        pen = [x, y]
        return (pen, path)

    def render(self, text, x=0, y=0):
        path = ''
        pen = list(self.origin)
        for word in self.iter_words(text):
            word = word.strip()
            if not word:
                continue
            while 1:
                word_width = self.get_width(word)
                if word_width + pen[0] > (self.size[0] + self.origin[0]):
                    #print("pen", pen, "word_width", word_width, "final x", word_width + pen[0], "size", self.size)
                    pen[0] = self.origin[0]
                    pen[1] += self.font.advance_y
                    if (pen[1] + self.font.height) > (self.size[1] + self.origin[1]):
                        raise self.TooSmall
                else:
                    #print("word", word, "pen", pen, "word_width", word_width, "final x", word_width + pen[0], "right margin", self.size[0] + self.origin[0])
                    break
            word += ' '
            (pen, _path) = self.path(pen, word)
            path += _path
        return path

_fs_cache = {}

def layout(fontfile, text, size, fontsize=None, offset=(0, 0)):
    fsc_hash = (text, size)
    path = None
    if fontsize == None and fsc_hash in _fs_cache:
        fontsize = _fs_cache[fsc_hash]
    else:
        fontsize = fontsize if fontsize != None else size[1]
    if fontsize == None:
        fontsize = int(math.ceil(math.sqrt(size[0] * size[1] / float(len(text)))))
    font = Font(fontfile)
    while fontsize:
        font.set_size(fontsize)
        _offset = (offset[0], offset[1] + fontsize)
        pt = PathText(font, origin=_offset, size=size)
        try:
            path = pt.render(text)
        except PathText.TooSmall:
            fontsize -= 1
            continue
        break
    if not path:
        raise RuntimeError, "layout impossible: %s" % text
    print("final fontsize", fontsize) 
    _fs_cache[fsc_hash] = fontsize
    return path
