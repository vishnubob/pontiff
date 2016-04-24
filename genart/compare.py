import PIL
from PIL import Image
from scipy.misc import imread, imresize
from scipy.linalg import norm
from scipy import sum, average

__all__ = ["CompareImages"]

class Image(object):
    def __init__(self, filename, size=None):
        self.filename = filename
        self.img = imread(self.filename).astype(float)
        if size != None:
            if size != self.img.size:
                self.img = imresize(self.img, size)
        self.to_grayscale()
        self.normalize()

    def to_grayscale(self):
        if len(self.img.shape) == 3:
            self.img = average(self.img, -1)  # average over the last axis (color channels)
        else:
            return self.img

    def normalize(self):
        rng = self.img.max() - self.img.min()
        minv = self.img.min()
        self.img = (self.img - minv) * 0xff / rng

    def __sub__(self, other):
        return self.img - other.img

class CompareImages(object):
    SizeCache = {}

    def __init__(self, target_fn):
        self.target_fn = target_fn
        self.target = Image(self.target_fn)

    def get_target(self, size):
        assert len(size) == 2
        if size not in self.SizeCache:
            img = Image(self.target_fn, size=size)
            self.SizeCache[size] = img
        return self.SizeCache[size]

    def compare_images(self, img1, img2):
        diff = img1 - img2
        # Manhattan norm
        m_norm = sum(abs(diff))
        # Zero norm
        z_norm = norm(diff.ravel(), 0)
        return (m_norm, z_norm)

    def compare(self, query_fn):
        query = Image(query_fn)
        target = self.get_target(query.img.shape[:2])
        (n_m, n_0) = self.compare_images(query, target)
        return (n_m, n_0, n_m / target.img.size, n_0 / target.img.size)
