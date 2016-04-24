import sys
import random
import uuid
import json
import os
from cairosvg import svg2png
from cairosvg.surface import PNGSurface
from simanneal import Annealer
import scipy
import StringIO
import time

__all__ = ["ImageAnnealer"] 

class ImageAnnealer(Annealer):
    def __init__(self, state, compare, factory, rootdir="/tmp"):
        super(ImageAnnealer, self).__init__(state)
        self.copy_strategy = "slice"
        self.compare = compare
        self.factory = factory
        self.best_energy = sys.maxint
        self.step = 0
        self.last_step = time.time()
        self.step_time = 0
        # directories
        self.runid = str(uuid.uuid4()).split('-')[0]
        self.rootdir = rootdir
        self.rundir = os.path.join(self.rootdir, self.runid)
        self.pngdir = os.path.join(self.rundir, "png")
        self.svgdir = os.path.join(self.rundir, "svg")
        self.statedir = os.path.join(self.rundir, "state")
        os.makedirs(self.pngdir)
        os.makedirs(self.svgdir)
        os.makedirs(self.statedir)
        msg = "Run directory is '%s'" % self.rundir
        print(msg)

    def step_callback(self, energy):
        self.step += 1
        """
        now = time.time()
        self.step_time += (now - self.last_step)
        self.last_step = now
        if (self.step % 10) == 0:
            avg_steptime = self.step_time / float(self.step)
            msg = "Steps: %d, Average step time: %.02f" % (self.step, avg_steptime)
            print(msg)
        """
        if energy < self.best_energy:
            self.best_energy = energy
            self.best_state = self.state

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
        img = self.factory.render_bitmap(self.state)
        scipy.misc.imsave(pngfn, img)
        #svg2png(url=svgfn, write_to=pngfn)
        # statefn
        statefn = stemfn + ".json"
        statefn = os.path.join(self.statedir, statefn)
        with open(statefn, 'w') as fh:
            json.dump(self.state, fh)

    def move(self):
        mode = random.choice([0, 1, 2])
        if mode == 0:
            # add
            for x in range(len(self.factory.rules)):
                val = random.random()
                self.state.append(val)
        elif mode == 1:
            # remove
            self.state = self.state[:-len(self.factory.rules)]
        elif mode == 2:
            # change
            idx = random.randint(0, len(self.state) - 1)
            self.state[idx] = random.random()

    def energy_path(self):
        stemfn = "energy"
        svg = self.factory.render(self.state)
        png = PNGSurface.convert(bytestring=str(svg))
        png = StringIO.StringIO(png)
        scores = self.compare.compare(png)
        energy = scores[0]
        self.step_callback(energy)
        return energy

    def energy(self):
        stemfn = "energy"
        img = self.factory.render_bitmap(self.state)
        scores = self.compare.compare(img)
        energy = scores[0]
        self.step_callback(energy)
        return energy
