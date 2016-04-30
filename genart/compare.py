import PIL.Image
import PIL.ImageOps
import PIL.ImageChops
from scipy.misc import imsave, imread, imresize
from scipy.linalg import norm
from scipy import sum, average
import numpy

__all__ = ["CompareImages"]

class Image(object):
    def __init__(self, thing, mode='L', size=None, name=None):
        if type(thing) in (str, unicode):
            self.filename = thing
            self.img = PIL.Image.open(self.filename)
        else:
            self.img = thing
        self.name = name if name != None else str(id(self))
        if size != None:
            if size != self.img.size:
                self.img = self.img.resize(size)
        if self.img.mode != mode:
            self.img = self.img.convert(mode=mode)
        if self.img.mode != "1":
            self.img = PIL.ImageOps.autocontrast(self.img)
        self.size = self.img.size

    def __sub__(self, other):
        return PIL.ImageChops.difference(self.img, other.img)
    
    def save(self, filename):
        self.img.save(filename)

class CompareImages(object):
    SizeCache = {}

    def __init__(self, target_fn, mode="L"):
        self.mode = mode
        self.target_fn = target_fn
        self.target = Image(self.target_fn, name="target", mode=self.mode)
        self.SizeCache[self.target.size] = self.target

    def get_target(self, size):
        assert len(size) == 2
        if size not in self.SizeCache:
            img = Image(self.target_fn, size=size, mode=self.mode)
            self.SizeCache[size] = img
        return self.SizeCache[size]

    def compare_images(self, img1, img2):
        diff = img1 - img2
        diff = numpy.array(diff)
        # Manhattan norm
        m_norm = sum(abs(diff))
        # Zero norm
        z_norm = norm(diff.ravel(), 0)
        return (m_norm, z_norm, m_norm / diff.size, z_norm / diff.size)

    def compare(self, query_fn):
        query = Image(query_fn, name="query", mode=self.mode)
        target = self.get_target(query.size)
        return self.compare_images(query, target)
