#!/usr/bin/env python
# coding: utf-8

import math
from enum import Enum

EMPTY = 'WHITE'
PEDESTRIAN = 'RED'
TARGET = 'YELLOW'
OBSTACLE = 'BLACK'


class Cell:
    # details of a cell
    def __init__(self, row, col, state):
        self.state = state
        self.row = row
        self.col = col

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.row == other.row and self.col == other.col and self.state == other.state
        else:
            return False


class System:
    # A collection of cells
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[Cell(i, j, EMPTY) for i in range(rows)] for j in range(cols)]
        self.pedestrian = []
        self.target = None
        self.obstacle = []
        
    def add_pedestrian(self, pedestrian: Cell):
        # mark a pedestrian in the grid
        self.pedestrian.append(pedestrian)
        self.grid[pedestrian.col][pedestrian.row] = pedestrian
        
    def remove_pedestrian(self, pedestrian: Cell):
        # remove a pedestrian from the grid
        self.grid[pedestrian.col][pedestrian.row] = Cell(pedestrian.col, pedestrian.row, EMPTY)
        self.pedestrian.remove(pedestrian)
        
    def add_target(self, target: Cell):
        # set the target of the grid, limit of 1 target
        self.target = target
        self.grid[target.col][target.row] = target
        
    def remove_target(self, target: Cell):
        # remove the target from the grid
        self.grid[target.col][target.row] = Cell(target.col, target.row, EMPTY)
        self.target = None
        
    def add_obstacle(self, obs: Cell):
        # add obstacle in the grid
        self.obstacle.append(obs)
        self.grid[obs.col][obs.row] = obs


def euclidean_distance(x: Cell, y: Cell):
    # distance between two cells
    return math.sqrt((x.row - y.row)**2 + (x.col - y.col)**2)



