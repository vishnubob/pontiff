#!/usr/bin/env python

import random
import uuid
import json
import os
from cairosvg import svg2png
from cairosvg.surface import PNGSurface
from simanneal import Annealer
import StringIO

__all__ = ["ImageAnnealer"] 

class ImageAnnealer(Annealer):
    def __init__(self, state, compare, factory, rootdir="/tmp"):
        super(ImageAnnealer, self).__init__(state)
        self.copy_strategy = "slice"
        self.compare = compare
        self.factory = factory
        self.runid = str(uuid.uuid4()).split('-')[0]
        self.rootdir = rootdir
        self.rundir = os.path.join(self.rootdir, self.runid)
        self.pngdir = os.path.join(self.rundir, "png")
        self.svgdir = os.path.join(self.rundir, "svg")
        self.statedir = os.path.join(self.rundir, "state")
        self.best_energy = sys.maxint
        self.step = 0
        os.makedirs(self.pngdir)
        os.makedirs(self.svgdir)
        os.makedirs(self.statedir)
        msg = "Run directory is '%s'" % self.rundir
        print(msg)

    def get_best_state(self):
        return self._best_state
    def set_best_state(self, state):
        self._best_state = state
        self.save(state=state)
    best_state = property(get_best_state, set_best_state)

    def save(self, stem=None, state=None):
        state = state if state != None else self.state
        stemfn = stem if stem != None else ("%06d" % self.step)
        # svg
        svgfn = stemfn + ".svg"
        svgfn = os.path.join(self.svgdir, svgfn)
        self.factory.render(self.state, svgfn)
        # png
        pngfn = stemfn + ".png"
        pngfn = os.path.join(self.pngdir, pngfn)
        svg2png(url=svgfn, write_to=pngfn)
        # statefn
        statefn = stemfn + ".json"
        statefn = os.path.join(self.statedir, statefn)
        with open(statefn, 'w') as fh:
            json.dump(self.state, fh)

    def move(self):
        mode = random.choice([0, 1, 2])
        if mode == 0:
            # add
            val = random.random()
            self.state.append(val)
        elif mode == 1:
            # remove
            del self.state[-1]
        elif mode == 2:
            # change
            idx = random.randint(0, len(self.state) - 1)
            self.state[idx] = random.random()

    def energy(self):
        self.step += 1
        stemfn = "energy"
        svg = self.factory.render(self.state)
        png = PNGSurface.convert(bytestring=str(svg))
        png = StringIO.StringIO(png)
        scores = self.compare.compare(png)
        energy = scores[0]
        if energy < self.best_energy:
            self.best_energy = energy
            self.best_state = self.state
        return energy
