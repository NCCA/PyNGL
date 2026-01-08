#!/usr/bin/env python3

import pathlib

import numpy as np

files = pathlib.Path(".").glob("*.npy")

data = {}
for f in files:
    data[str(f.stem)] = np.load(f)
print(data.keys())


np.savez_compressed("Primitives", **data)

loaded = np.load("Primitives.npz")
print(loaded)
print(loaded["dragon"])
