#!/usr/bin/env python

import json
import argparse
from genart import *

def load_population(args):
    popfn = args.population
    if popfn == None:
        return None
    with open(popfn) as fh:
        return json.load(fh)

def bootstrap(args):
    size = (args.width, args.height)
    target_size = tuple([int(val * args.ratio) for val in size])
    if target_size == size:
        target_size = None
    factory = FaceFactory(args.fontfile, size=size)
    compare = CompareImages(args.target, mode=args.mode)
    env = Environment(compare, factory, rootdir=args.rootdir, runid=args.runid, target_size=target_size)
    pop = load_population(args)
    pool = None
    if args.threads > 1:
        pool = ArtistPool(args)
    ga = GA_Runner(env, population=args.population, mutpb=args.mutpb, cxpb=args.cxpb, keep=args.keep, initsize=args.initsize, popsize=args.popsize, pool=pool)
    return ga

def get_cli():
    parser = argparse.ArgumentParser(description='genart')
    parser.add_argument('--target', '-t', required=True)
    parser.add_argument('--fontfile', '-f', required=True)
    parser.add_argument('--width', '-W', default=600, type=int)
    parser.add_argument('--height', '-H', default=600, type=int)
    parser.add_argument('--ratio', default=1, type=float)
    parser.add_argument('--rootdir', '-r', default="/tmp/pontiff")
    parser.add_argument('--runid', '-R', default=None)
    parser.add_argument('--population', '-p', default=None)
    parser.add_argument('--mode', '-m', type=str, default="L")
    parser.add_argument('--threads', type=int, default="-1")
    # ga args
    parser.add_argument('--mutpb', default=0.2, type=float)
    parser.add_argument('--cxpb', default=0.5, type=float)
    parser.add_argument('--keep', default=5, type=int)
    parser.add_argument('--initsize', default=1000, type=int)
    parser.add_argument('--popsize', default=300, type=int)
    parser.add_argument('--ngen', default=100, type=int)

    #
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = get_cli()
    print(args)
    ga = bootstrap(args)
    ga.run(args.ngen)
