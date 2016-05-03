import multiprocessing as mp
import operator
from . factory import *
from . environment import *
from . compare import *

__all__ = ["ArtistPool"]

class Artist(mp.Process):
    def __init__(self, args, outq):
        self.inq = mp.JoinableQueue()
        self.outq = outq
        size = (args.width, args.height)
        target_size = tuple([int(val * args.ratio) for val in size])
        if target_size == size:
            target_size = None
        factory = FaceFactory(args.fontfile, size=size)
        compare = CompareImages(args.target, mode=args.mode)
        self.env = Environment(compare, factory, rootdir=args.rootdir, runid=args.runid, target_size=target_size)
        super(Artist, self).__init__()

    def run(self):
        while 1:
            individual = self.inq.get()
            self.inq.task_done()
            if individual == None:
                self.inq.join()
                break
            (idx, individual) = individual
            res = self.evaluate(individual)
            self.outq.put((idx, res))

    def evaluate(self, individual):
        return self.env.evaluate(individual)

class ArtistPool(object):
    def __init__(self, args):
        self.inq = mp.JoinableQueue()
        self.artists = [Artist(args, self.inq) for idx in range(args.threads)]
        for artist in self.artists:
            artist.start()

    def evaluate(self, individuals):
        for (idx, individual) in enumerate(individuals):
            individual = list(individual)
            aidx = idx % len(self.artists)
            artist = self.artists[aidx]
            artist.inq.put((idx, individual))
        results = [None] * len(individuals)
        while None in results:
            (idx, score) = self.inq.get()
            self.inq.task_done()
            results[idx] = (score, )
        return results
    
    def map(self, functor, *args):
        funcname = functor()
        func = getattr(self, funcname)
        return func(*args)
