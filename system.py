#!/usr/bin/env python
# coding: utf-8
import heapq
import math
import sys
import numpy as np
from enum import Enum
from typing import Union, Tuple

EMPTY = 'WHITE'
PEDESTRIAN = 'RED'
TARGET = 'YELLOW'
OBSTACLE = 'BLACK'

R_MAX = 2


class Cell:
    # details of a cell
    def __init__(self, col, row, state):
        self.visited = False
        self.state = state
        self.row = row
        self.col = col
        self.next_cell = None
        self.distanceFromTarget = sys.maxsize
        self.adjacent_cells = []

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

    def set_distance(self, dist: float):
        self.distanceFromTarget = dist

    def get_distance(self):
        return float(self.distanceFromTarget)

    def set_visited(self):
        self.visited = True

    def set_previous(self, cell):
        self.next_cell = cell


class System:
    # A collection of cells
    def __init__(self, cols, rows):
        self.rows = rows
        self.cols = cols
        self.grid = [[Cell(i, j, EMPTY) for i in range(cols)] for j in range(rows)]
        self.pedestrian = []  # Stores tuples of coordinate in the form (x: col, y: row)
        self.target: Cell = None
        self.obstacle = []  # Stores tuples of coordinate in the form (x: col, y: row)

    def __str__(self):
        for row in self.grid:
            print("\n")
            for cell in row:
                print(str(cell))

    def add_pedestrian_at(self, coordinates: tuple):
        # mark a pedestrian in the grid
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.pedestrian.append(cell)
        cell.state = PEDESTRIAN

    def remove_pedestrian_at(self, coordinates: tuple):
        # remove a pedestrian from the grid
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.pedestrian.remove(cell)
        cell.state = EMPTY

    def add_target_at(self, coordinates: tuple):
        # set the target of the grid, limit of 1 target
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.target = cell
        cell.state = TARGET
        return cell

    # def remove_target_at(self, coordinates: tuple):
    #     # remove the target from the grid
    #     cell = self.grid[coordinates[0]][coordinates[1]]
    #     self.target = cell
    #     cell.state = EMPTY

    def add_obstacle_at(self, coordinates: tuple):
        # add obstacle in the grid
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.obstacle.append(cell)
        cell.state = OBSTACLE

    def update_sys(self):

        # for pedestrian in self.pedestrian:

        for cell in self.pedestrian:
            if cell.next_cell == self.target:
                continue
            self.pedestrian.remove(cell)
            self.pedestrian.append(cell.next_cell)
            cell.state = EMPTY
            cell.next_cell.state = PEDESTRIAN
            # Add get safe distance from other pedestrians here

    def no_obstacle_avoidance_update_sys(self):
        for cell in self.pedestrian:
            for adjacent in get_adjacent(cell, self):
                if adjacent.distanceFromTarget < cell.distanceFromTarget:
                    cell.next_cell = adjacent
            self.pedestrian.remove(cell)
            self.pedestrian.append(cell.next_cell)
            cell.state = EMPTY
            cell.next_cell.state = PEDESTRIAN


# def pedestrian_interaction_distance(current_cell: Cell):
#     if current_cell.state == PEDESTRIAN:
#         if distance_from_other_pedestrian < r_max:
#             return np.exp(1/())


def euclidean_distance(x: Cell, y: Cell):
    # distance between two cells
    return math.sqrt((x.row - y.row) ** 2 + (x.col - y.col) ** 2)


def get_weight(current_cell: Cell, next_cell: Cell):
    if next_cell.state == OBSTACLE:
        return float(sys.maxsize)
    elif next_cell.state == TARGET:
        return 0.0
    elif next_cell.state == PEDESTRIAN:
        return 5.0
    return euclidean_distance(current_cell, next_cell)


def get_adjacent(cell, system):
    """
    Returns list of all the adjacent cells
    :param: Cell, System:
    :return: --> Cell
    """
    rows = system.rows
    cols = system.cols
    row = cell.row
    col = cell.col
    adjacent_cell = []
    if rows != (row + 1):
        adjacent_cell.append(system.grid[row + 1][col])
        if col + 1 != cols:
            adjacent_cell.append(system.grid[row + 1][col + 1])
        if col - 1 >= 0:
            adjacent_cell.append(system.grid[row + 1][col - 1])
    if row - 1 >= 0:
        adjacent_cell.append(system.grid[row - 1][col])
        if col + 1 != cols:
            adjacent_cell.append(system.grid[row - 1][col + 1])
        if col - 1 >= 0:
            adjacent_cell.append(system.grid[row - 1][col - 1])
    if col + 1 != cols:
        adjacent_cell.append(system.grid[row][col + 1])
    if col - 1 >= 0:
        adjacent_cell.append(system.grid[row][col - 1])

    return adjacent_cell


def evaluate_cell_distance(system: System):
    system.target.set_distance(0)
    unvisited_queue = [(system.target.get_distance(), system.target)]

    while len(unvisited_queue):
        unvisited = heapq.heappop(unvisited_queue)
        current_cell = unvisited[1]
        # current_cell = heapq.heappop(unvisited_queue)
        current_cell.set_visited()

        for next_cell in get_adjacent(current_cell, system):
            if next_cell.visited:
                continue
            new_dist = current_cell.get_distance() + get_weight(current_cell, next_cell)

            if new_dist < next_cell.get_distance():
                next_cell.set_distance(new_dist)
                next_cell.set_previous(current_cell)
                heapq.heappush(unvisited_queue, (next_cell.get_distance(), next_cell))

        # while len(unvisited_queue):
        #     heapq.heappop(unvisited_queue)
        #
        # for row in system.grid:
        #     for cell in row:
        #         if not cell.visited:
        #             unvisited_queue.append((cell.get_distance(), cell))
        # heapq.heapify(unvisited_queue)

def no_obstacle_avoidance(system: System):
    for row in system.grid:
        for cell in row:
            cell.distanceFromTarget = euclidean_distance(cell, system.target)
            if cell.state == OBSTACLE:
                cell.distanceFromTarget = sys.maxsize


