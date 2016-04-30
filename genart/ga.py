import random
import json
import os

import numpy
import multiprocessing
from deap import algorithms
from deap import base
from deap import creator
from deap import tools

from . __init__ import *

class EvaluateWrapper(object):
    def __init__(self, env):
        self.env = env
    def __call__(self, state):
        return (self.env.evaluate(state), )

class GA_Runner(object):
    def __init__(self, env, population=None, mutpb=0.2, cxpb=0.5, keep=5, initsize=1000, popsize=300, threads=-1):
        self.env = env
        self.mutpb = mutpb
        self.cxpb = cxpb
        self.keep = keep
        self.popsize = popsize
        self.population = population
        self.initsize = initsize * 5
        self.threads = threads
        self.pool = None
        if self.threads > 1:
            self.pool = multiprocessing.Pool(self.threads)
        self.bootstrap()

    def evaluate(self, state):
        score = self.env.evaluate(state)
        return (score, )

    def mutate(self, state):
        state = self.env.mutate(state)
        new = creator.Individual(state)
        return (new, )

    def crossover(self, *args):
        return map(creator.Individual, self.env.crossover(*args))
    
    def bootstrap(self):
        # class factories
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        # wrappers
        eval_wrapper = EvaluateWrapper(self.env)

        # toolbox
        self.toolbox = base.Toolbox()
        self.toolbox.register("gene", random.random)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self.toolbox.gene, self.initsize)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("mate", self.crossover)
        self.toolbox.register("mutate", self.mutate)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        self.toolbox.register("evaluate", eval_wrapper)
        if self.pool:
            self.toolbox.register("map", self.pool.map)

        # stats
        score_stats = tools.Statistics(lambda ind: ind.fitness.values)
        len_stats = tools.Statistics(lambda ind: len(ind) / 5.0)
        self.stats = tools.MultiStatistics(length=len_stats, score=score_stats)
        self.stats.register("avg", numpy.mean)
        self.stats.register("std", numpy.std)
        self.stats.register("min", numpy.min)
        self.stats.register("max", numpy.max)

        # members
        if self.population == None:
            self.population = self.toolbox.population(n=self.popsize)
        self.hof = tools.HallOfFame(self.keep)

    def evolve(self, ngen):
        (self.population, log) = algorithms.eaSimple(self.population, 
                    self.toolbox, cxpb=self.cxpb, mutpb=self.mutpb, ngen=ngen, 
                    stats=self.stats, halloffame=self.hof, verbose=True)
        return (self.population, log)
    
    def run(self, ngen):
        gencount = 0
        while 1:
            self.write(gencount)
            self.evolve(ngen)
            gencount += ngen

    def write(self, generation):
        popfn = "population_g%06d.json" % generation
        popfn = os.path.join(self.env.statedir, popfn)
        with open(popfn, 'w') as fh:
            json.dump(self.population, fh)
        for top in self.hof:
            score = top.fitness.values[0]
            stem = "g%06d_s%010d" % (generation, score)
            self.env.save(top, stem)

if __name__ == "__main__":
    run = 0
    while 1:
        run += 1
        (pop, log, hof) = evolve(pop)
        ann.state = hof[-1]
        ann.save("%d-final" % run)
        best = hof[:]
        pop = toolbox.population(n=300)
        pop.extend(best)
