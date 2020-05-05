#!/usr/bin/env python
# coding: utf-8


import heapq
import math
import sys
from enum import Enum
import numpy as np
import pylab as plt
import skfmm

EMPTY = 'WHITE'
PEDESTRIAN = 'RED'
TARGET = 'YELLOW'
OBSTACLE = 'BLACK'


class System:
    #A collection of cells
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[Cell(i, j) for i in range(rows)] for j in range(cols)]
        self.pedestrian = []
        self.target = None
        self.obstacle = []
        

    def __str__(self):
        for row in self.grid:
            print("\n")
            for cell in row:
                print(str(cell))


    def add_pedestrian_at(self, pedestrian):
        #mark a pedestrian in the grid 
        self.grid[pedestrian[0]][pedestrian[1]].state = PEDESTRIAN
        self.pedestrian.append(pedestrian)
        
    def remove_pedestrian_at(self, pedestrian):
        #remove a pedestrian from the grid 
        if pedestrian in self.pedestrian:
            self.grid[pedestrian[0]][pedestrian[1]].state = EMPTY
            self.pedestrian.remove(pedestrian)
        else:
            print("No pedestrian found!")
        
    def add_target_at(self, target):
        #set the target of the grid, limit of 1 target
        if self.target is not None:
            self.grid[self.target[0]][self.target[1]].state = EMPTY
        self.target = target
        self.grid[target[0]][target[1]].state = TARGET
        return self.grid[target[0]][target[1]]
        
    def remove_target_at(self, target = None):
        #remove the target from the grid
        if target is not None:
            if self.target == target:
                self.target = None
            else:
                print("No such target found!")
        else:
            self.target = None
        
    def add_obstacle_at(self, obs):
        #add obstacle in the grid
        self.grid[obs[0]][obs[1]].state = OBSTACLE
        self.obstacle.append(obs)

    def remove_obstacle_at(self, obs):
        #remove obstacle from the list
        self.grid[obs[0]][obs[1]].state = EMPTY
        self.obstacle.remove(obs)

    def update_sys(self):
        
        for p in self.pedestrian:
            
            path = self.calc_fmm(p)
            if self.grid[path[0][0]][path[0][1]].state == TARGET:
                continue
            self.remove_pedestrian_at(p)
            self.add_pedestrian_at(path[0])
            print(self.grid[self.pedestrian[0][0]][self.pedestrian[0][1]].state)
            
            

    def calc_fmm(self, p):
        t_grid = np.array(np.ones_like(self.grid), dtype = np.double)
        mask = np.array(0 * np.ones_like(self.grid), dtype = bool)
        t_grid[self.target[0], self.target[1]] = -1
        for i in self.obstacle:
            mask[i[0]][i[1]] = True
        phi = np.ma.MaskedArray(t_grid, mask)
        d = skfmm.distance(phi)
        
        #print(d)

        return self.calc_fmm_path(d, p)

    def calc_fmm_path(self, distance, p):
        
        print(p, self.target, self.obstacle)
        print(distance[p[0], p[1]])
        path = []
        while self.target != p:
            p_adj_cell = get_adjacent(self.grid[p[0]][p[1]], self)
            p_adj = [(i.row, i.col) for i in p_adj_cell if (i.row, i.col) not in path]
            
            #print(p_adj)
            p_adj = np.asarray(p_adj)
            d = distance[p_adj[:,0], p_adj[:,1]]
            idx = np.where(distance == np.amin(d))
                        
            idx = list(zip(idx[0], idx[1]))
            #print(idx)
            
            idx = [i for i in idx if i in p_adj]
            path.append(idx[0])
            #print(idx[0])
            p = idx[0]
            
        return path
        
def euclidean_distance(x, y):
    #this one has some problems
    #distance between a tuple of two coordinates
    return math.sqrt((x[0]-y[0])**2 + (x[1]-y[1])**2)
    
    
class Cell:
    #details of a cell
    #state of cell
    # EMPTY : empty
    # PEDESTRIAN : pedestrian
    # TARGET : target
    # OBSTACLE : obstacle
    def __init__(self, row, col, state = EMPTY):
        self.visited = False
        self.state = state
        self.row = row
        self.col = col
        self.distanceFromTarget = sys.maxsize
        self.adjacent_cells = []
        self.fmm_state = -1
        
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.row == other.row and self.col == other.col and self.state == other.state
        else:
            return False

    def __lt__(self, other):
        return self.distanceFromTarget < other.distanceFromTarget

    def __str__(self):
        return "|(" + str(self.col) + "," + str(self.row) + ") Next Cell: " + str(self.next_cell.col) + "," \
               + str(self.next_cell.row) + ")|"

    def set_distance(self, dist: int):
        self.distanceFromTarget = dist

    def get_distance(self):
        return self.distanceFromTarget

    def set_visited(self):
        self.visited = True

    def set_previous(self, cell):
        self.previous_cell = cell
        
        
def get_weight(cell: Cell):
    if cell.state == OBSTACLE:
        return sys.maxsize
    elif cell.state == TARGET:
        return 0
    elif cell.state == PEDESTRIAN:
        return 5
    return 1


def get_adjacent(cell, system):
    """
    Returns list of all the adjacent cells
    :param: Cell, System:
    :return: --> Cell, coord
    """
    rows = system.rows
    cols = system.cols
    row = cell.row
    col = cell.col
    adjacent_cell = []
    adjacent_cell_coord = []
    if rows != (row+1):
        adjacent_cell.append(system.grid[row+1][col])
        if col + 1 != cols:
            adjacent_cell.append(system.grid[row+1][col+1])
        if col - 1 >= 0:
            adjacent_cell.append(system.grid[row+1][col-1])
    if row - 1 >= 0:
        adjacent_cell.append(system.grid[row-1][col])
        if col + 1 != cols:
            adjacent_cell.append(system.grid[row-1][col+1])
        if col - 1 >= 0:
            adjacent_cell.append(system.grid[row-1][col-1])
    if col + 1 != cols:
        adjacent_cell.append(system.grid[row][col+1])
    if col - 1 >= 0:
        adjacent_cell.append(system.grid[row][col-1])
        
    return adjacent_cell


def evaluate_cell_distance(system: System, target: Cell):
    target.set_distance(0)
    unvisited_queue = [(target.get_distance(), target)]

    while len(unvisited_queue):
        unvisited = heapq.heappop(unvisited_queue)
        current_cell = unvisited[1]
        # current_cell = heapq.heappop(unvisited_queue)
        current_cell.set_visited()
        adj_cell = get_adjacent(current_cell, system)
        for next_cell in adj_cell:
            if next_cell.visited:
                continue
            new_dist = current_cell.get_distance() + get_weight(next_cell)

            if new_dist < next_cell.get_distance():
                next_cell.set_distance(new_dist)
                next_cell.set_previous(current_cell)

        while len(unvisited_queue):
            heapq.heappop(unvisited_queue)

        for row in system.grid:
            for cell in row:
                if not cell.visited:
                    unvisited_queue.append((cell.get_distance(), cell))
        heapq.heapify(unvisited_queue)




    

        


