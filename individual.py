#!/usr/bin/env python

import random
from genart import *

def random_state(size):
    count = size * 5
    state = [random.random() for x in range(count)]
    return state

def run():
    font_filename = "fonts/OpenSans-Regular.ttf"
    compare = CompareImages("target.png")
    init_state = random_state(1000)
    size = (600, 600)
    #target_size = (100, 100)
    target_size = None
    factory = FaceFactory(font_filename, size, target_size=target_size)
    ann = ImageAnnealer(init_state, compare, factory, rootdir="/tmp/pontiff")
    ann.save(stem="initial")
    ann.anneal()
    ann.save(stem="final")

if __name__ == "__main__":
    run()
