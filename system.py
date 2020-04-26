#!/usr/bin/env python
# coding: utf-8



import math




class System:
    #A collection of cells
    def __init__(self, rows, cols):
        self.grid = [[(0) for i in range(rows)] for j in range(cols)]
        self.pedastrian = []
        self.target = None
        self.obstacle = []
        
    def add_pedastrian(self, pedastrian):
        #mark a pedastrian in the grid 
        self.pedastrian.append(pedastrian)
        
    def remove_pedastrian(self, pedastrian):
        #remove a pedastrian from the grid 
        self.pedastrian.remove(pedastrian)
        
    def add_target(self, target):
        #set the target of the grid, limit of 1 target
        self.target = target
        
    def remove_target(self, target):
        #remove the target from the grid
        self.target = None
        
    def add_obstacle(self, obs):
        #add obstacle in the grid
        self.obstacle.append(obs)
        
    def euclidean_distance(x, y):
        #distance between a tuple of two coordinates
        return math.sqrt((x[0]-y[0])**2 + (x[1]-y[1])**2)
    
    
class Cell:
    #details of a cell
    def __init__(self, row, col, state = 0):
        self.state = state
        self.row = row
        self.col = col
        





