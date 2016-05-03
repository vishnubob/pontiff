import random
import math
import uuid
import json
import os
from cairosvg import svg2png
import scipy

__all__ = ["Environment"] 

def weighted_choice(choices):
    total = sum(weight for choice, weight in choices)
    val = random.uniform(0, total)
    upto = 0
    for (choice, weight) in choices:
        if upto + weight >= val:
            return choice
        upto += weight
    assert False, "Shouldn't get here"

class Environment(object):
    def __init__(self, compare, factory, rootdir="/tmp", runid=None, add_weight=1, remove_weight=1, change_weight=3, size_limit=None, target_size=None):
        self.compare = compare
        self.factory = factory
        self.add_weight = add_weight
        self.remove_weight = remove_weight
        self.change_weight = change_weight
        self.size_limit = size_limit
        self.target_size = target_size
        # directories
        self.runid = runid if runid != None else str(uuid.uuid4()).split('-')[0]
        self.rootdir = rootdir
        self.rundir = os.path.join(self.rootdir, self.runid)
        self.pngdir = os.path.join(self.rundir, "png")
        self.svgdir = os.path.join(self.rundir, "svg")
        self.statedir = os.path.join(self.rundir, "state")
        dirs = [self.pngdir, self.svgdir, self.statedir]
        for dirname in dirs:
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
        msg = "Run directory is '%s'" % self.rundir
        print(msg)

    def save(self, state, stemfn):
        # svg
        svgfn = stemfn + ".svg"
        svgfn = os.path.join(self.svgdir, svgfn)
        self.factory.render(state, svgfn)
        # png
        pngfn = stemfn + ".png"
        pngfn = os.path.join(self.pngdir, pngfn)
        img = self.factory.render_bitmap(state)
        scipy.misc.imsave(pngfn, img)
        #svg2png(url=svgfn, write_to=pngfn)
        # statefn
        statefn = stemfn + ".json"
        statefn = os.path.join(self.statedir, statefn)
        with open(statefn, 'w') as fh:
            json.dump(state, fh)

    def mutate(self, state):
        (add, remove, change) = (0, 1, 2)
        choices = {
            add: self.add_weight,
            remove: self.remove_weight,
            change: self.change_weight,
        }
        if self.size_limit and len(state) > self.size_limit:
            del choices[add]
        mode = weighted_choice(choices.items())
        entities = len(state) / len(self.factory.rules)
        marker = random.randint(0, entities - 1) * len(self.factory.rules)
        if mode == add:
            # add
            new_entity = [random.random() for x in range(len(self.factory.rules))]
            state = state[:marker] + new_entity + state[marker:]
        elif mode == remove:
            # remove
            state[marker:marker + len(self.factory.rules)] = []
        elif mode == change:
            # change
            new_entity = [random.random() for x in range(len(self.factory.rules))]
            state[marker:marker + len(self.factory.rules)] = new_entity
        return state

    def evaluate(self, state):
        #img = self.factory.render_bitmap(state, mode=self.compare.mode)
        img = self.factory.render_bitmap(state)
        if self.target_size != None:
            img = img.resize(self.target_size)
        scores = self.compare.compare(img)
        energy = scores[0]
        return energy
    
    def crossover(self, ind1, ind2):
        size = min(len(ind1), len(ind2)) / len(self.factory.rules)
        cxpoint1 = random.randint(0, size) * len(self.factory.rules)
        cxpoint2 = random.randint(0, size - 1) * len(self.factory.rules)
        ind1[cxpoint1:cxpoint2], ind2[cxpoint1:cxpoint2] = ind2[cxpoint1:cxpoint2], ind1[cxpoint1:cxpoint2]
        return (ind1, ind2)

