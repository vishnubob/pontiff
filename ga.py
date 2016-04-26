import array
import random

import numpy

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

from genart import *
import os

font_filename = os.path.abspath(os.path.join(os.getcwd(), "fonts/OpenSans-Regular.ttf"))
assert os.path.isfile(font_filename)
target_fn = "target.png"
target_fn = os.path.join(os.getcwd(), target_fn)
assert os.path.isfile(target_fn)
compare = CompareImages(target_fn)
size = (600, 600)
target_size = None
init_state = []

factory = FaceFactory(font_filename, size, target_size=target_size)
ann = ImageAnnealer(init_state, compare, factory, rootdir="/tmp/pontiff")
#ann.save(stem="initial")

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()

def energy(individual):
    ann.state = individual
    energy = ann.energy()
    return (energy, )

def mutate(individual):
    new = ann.move(individual)
    new = creator.Individual(new)
    return (new, )

# Attribute generator
toolbox.register("gene", random.random)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.gene, 1000)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("evaluate", energy)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", mutate)
toolbox.register("select", tools.selTournament, tournsize=3)

def evolve(pop):
    hof = tools.HallOfFame(5)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=100, 
                                   stats=stats, halloffame=hof, verbose=True)
    
    return pop, log, hof

if __name__ == "__main__":
    #random.seed(64)
    run = 0
    pop = toolbox.population(n=300)
    while 1:
        run += 1
        (pop, log, hof) = evolve(pop)
        ann.state = hof[-1]
        ann.save("%d-final" % run)
        best = hof[:]
        pop = toolbox.population(n=300)
        pop.extend(best)
