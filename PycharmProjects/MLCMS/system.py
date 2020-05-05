#!/usr/bin/env python
# coding: utf-8
import heapq
import math
import sys
import numpy as np
import skfmm

EMPTY = 'WHITE'
PEDESTRIAN = 'RED'
TARGET = 'YELLOW'
OBSTACLE = 'BLUE'

R_MAX = 2

class Cell:
    # details of a cell
    def __init__(self, parent, col, row, state):
        self.system = parent
        self.visited = False
        self.state = state
        self.row = row
        self.col = col
        self.next_cell = None
        self.distance_utility = float(sys.maxsize)
        self.pedestrian_utility = 0.0
        self.adjacent_cells = []
        self.wait_fmm_penalty = 1

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.row == other.row and self.col == other.col and self.state == other.state
        else:
            return False

    def __lt__(self, other):
        return self.distance_utility < other.distance_utility

    def __str__(self):
        return "|(" + str(self.row) + "," + str(self.col) + ") Next Cell: " + str(self.next_cell.row) + "," \
               + str(self.next_cell.col) + ")|"

    def set_distance(self, dist: float):
        self.distance_utility = dist

    def get_utility(self):
        return float(self.distance_utility)

    def set_visited(self):
        self.visited = True

    def set_next(self, cell):
        self.next_cell = cell

    def get_adjacent(self):
        """
        Returns list of all the adjacent cells
        :param: Cell, System:
        :return: --> Cell
        """
        rows = self.system.rows
        cols = self.system.cols
        row = self.row
        col = self.col
        adjacent_cell = []
        if row + 1 < rows:
            adjacent_cell.append(self.system.grid[row + 1][col])
            if col + 1 < cols:
                adjacent_cell.append(self.system.grid[row + 1][col + 1])
            if col - 1 >= 0:
                adjacent_cell.append(self.system.grid[row + 1][col - 1])
        if row - 1 >= 0:
            adjacent_cell.append(self.system.grid[row - 1][col])
            if col + 1 < cols:
                adjacent_cell.append(self.system.grid[row - 1][col + 1])
            if col - 1 >= 0:
                adjacent_cell.append(self.system.grid[row - 1][col - 1])
        if col + 1 < cols:
            adjacent_cell.append(self.system.grid[row][col + 1])
        if col - 1 >= 0:
            adjacent_cell.append(self.system.grid[row][col - 1])

        return adjacent_cell

    def get_adjacent_minus_obstacles(self):
        return [cell for cell in self.adjacent_cells if cell not in self.system.obstacles]

    def get_pedestrian_grid(self, r_max):
        ped_grid_cells = []
        for row in self.system.grid[max(0,self.row - r_max): min(self.system.rows, self.row + r_max + 1)]:
            for cell in row[max(0, self.col - r_max):min(self.system.cols, self.col + r_max + 1)]:
                if cell not in self.system.obstacles:
                    ped_grid_cells.append(cell)
        return ped_grid_cells


class System:
    # A collection of cells
    def __init__(self, cols, rows):
        self.rows = rows
        self.cols = cols
        self.grid = [[Cell(self, i, j, EMPTY) for i in range(cols)] for j in range(rows)]
        self.pedestrian = []  # Stores tuples of coordinate in the form (x: col, y: row)
        self.target: Cell = None
        self.obstacles = []  # Stores tuples of coordinate in the form (x: col, y: row)
        self.fmm_distance = np.array([])
        self.tt = np.array([])


        for col in self.grid:
            for cell in col:
                cell.adjacent_cells = cell.get_adjacent()

    def __str__(self):
        for row in self.grid:
            print("\n")
            for cell in row:
                print(str(cell))



    def print_distance_utilities(self):
        for row in self.grid:
            for cell in row:
                if cell.distance_utility >= sys.maxsize:
                    print(" MAX ", end="  ")
                else:
                    print("{:05.2f}".format(cell.distance_utility), end="  ")
            print()
        print()

    def print_pedestrian_utilities(self):
        for row in self.grid:
            for cell in row:
                if cell.pedestrian_utility >= sys.maxsize:
                    print(" MAX ", end="  ")
                else:
                    print("{:05.2f}".format(cell.pedestrian_utility), end="  ")
            print()
        print()

    def print_utilities(self):
        for row in self.grid:
            for cell in row:
                if cell.pedestrian_utility + cell.distance_utility >= sys.maxsize:
                    print(" MAX ", end="  ")
                else:
                    print("{:05.2f}".format(cell.pedestrian_utility + cell.distance_utility), end="  ")
            print()
        print()

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
        # add obstacles in the grid
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.obstacles.append(cell)
        cell.state = OBSTACLE

    def no_obstacle_avoidance_update_sys(self):
        for cell in self.pedestrian:
            if cell is not None:
                for adjacent in cell.adjacent_cells:
                    if adjacent.distance_utility < cell.distance_utility:
                        cell.next_cell = adjacent
                if cell.next_cell is None:
                    print('The pedestrian is stuck')
                    continue
            self.pedestrian.remove(cell)
            self.pedestrian.append(cell.next_cell)
            cell.state = EMPTY
            cell.next_cell.state = PEDESTRIAN

    def get_next_pedestrian_cells(self):
        for ped in self.pedestrian:
            add_pedestrian_utilities(ped)
            # ped.pedestrian_utility = float(sys.maxsize)
        # self.print_pedestrian_utilities()
        # self.print_utilities()

        next_cells = []
        for ped in self.pedestrian:
            next_cell = ped
            for neighbour in [cell for cell in ped.get_adjacent_minus_obstacles() if cell not in next_cells + self.pedestrian]:
                if neighbour.distance_utility + neighbour.pedestrian_utility <= next_cell.distance_utility + next_cell.pedestrian_utility and neighbour.state != PEDESTRIAN:
                    next_cell = neighbour
                    next_cells.append(next_cell)
            ped.set_next(next_cell)
            # print(ped)
        for ped in self.pedestrian:
            reset_pedestrian_utilities(ped)
            # ped.pedestrian_utility = float(sys.maxsize)

    def update_sys(self):
        new_peds = []
        self.get_next_pedestrian_cells()
        for ped in self.pedestrian:
            if ped.next_cell == self.target:
                continue
            ped.state = EMPTY
            ped.next_cell.state = PEDESTRIAN
            # self.pedestrian.remove(ped)
            new_peds.append(ped.next_cell)
        self.pedestrian = new_peds

    def evaluate_cell_utilities(self):
        self.target.set_distance(0)
        unvisited_queue = [(self.target.get_utility(), self.target)]

        while len(unvisited_queue):
            unvisited = heapq.heappop(unvisited_queue)
            current_cell = unvisited[1]
            # current_cell = heapq.heappop(unvisited_queue)
            current_cell.set_visited()

            for next_cell in current_cell.get_adjacent_minus_obstacles():
                if next_cell.visited:
                    continue
                # new_dist = current_cell.get_utility() + get_distance_utilities(current_cell, next_cell)
                # new_dist = current_cell.get_utility() + 1
                new_dist = current_cell.get_utility() + get_euclidean_distance(current_cell, next_cell)

                if new_dist < next_cell.get_utility():
                    next_cell.set_distance(new_dist)
                    # next_cell.set_previous(current_cell)
                    heapq.heappush(unvisited_queue, (next_cell.get_utility(), next_cell))

    def no_obstacle_avoidance(self):
        for row in self.grid:
            for cell in row:
                cell.distance_utility = get_euclidean_distance(cell, self.target)
                if cell.state == OBSTACLE:
                    cell.distance_utility = sys.maxsize

    def update_sys_fmm(self):
        ped = [(p.row, p.col) for p in self.pedestrian]
        wait = []

        for p in ped:
            # print("reached here")

            path, tt = self.calc_fmm(p, self.grid[p[0]][p[1]].wait_fmm_penalty)

            # print(path)

            if self.grid[path[0][0]][path[0][1]].state == PEDESTRIAN:
                # Can be thought of as the level of patience
                self.grid[p[0]][p[1]].wait_fmm_penalty += 0.001
                print(p, "--> Wait")
                continue
            if self.grid[path[0][0]][path[0][1]] == self.target:
                continue
            print(p, " --> ", path[0], "Travel Time = ", tt)
            self.remove_pedestrian_at(p)
            self.add_pedestrian_at(path[0])
            # print("reached here")
            # print(self.grid[self.pedestrian[0][0]][self.pedestrian[0][1]].state)

    def calc_fmm(self, p, wait=1):
        if self.fmm_distance.size == 0:
            t_grid = np.array(np.ones_like(self.grid), dtype=np.double)
            mask = np.array(0 * np.ones_like(self.grid), dtype=bool)
            t_grid[self.target.row, self.target.col] = -1
            for i in self.obstacles:
                mask[i.row][i.col] = True
            phi = np.ma.MaskedArray(t_grid, mask)
            self.fmm_distance = skfmm.distance(phi)
            speed = 1.3 * np.ones_like(t_grid)
            self.tt = skfmm.travel_time(phi, speed, dx=0.4)
        #print(t)
        for i in self.obstacles:
            self.fmm_distance[i.row][i.col] = sys.maxsize
        d = np.copy(self.fmm_distance)
        t = np.copy(self.tt)
        for j in self.pedestrian:
            d[j.row, j.col] *= ((wait*(1 + (1/(d[j.row, j.col])*10))) + 1/d[j.row, j.col])
        return self.calc_fmm_path(d, t, p)

    def calc_fmm_path(self, distance, t, p):

        # print(p)
        path = []
        p_adj_cell = self.grid[p[0]][p[1]].get_adjacent()
        p_adj = [(i.row, i.col) for i in p_adj_cell]
        p_copy = p_adj

        p_adj = np.asarray(p_adj)
        row_idx = p_adj[:, 0]
        col_idx = p_adj[:, 1]
        d = distance[row_idx, col_idx]

        idx = np.where(distance == np.amin(d))
        idx = tuple(zip(idx[0], idx[1]))
        tt = t[idx[0]]
        idx = [i for i in idx if i in p_copy]

        path.append(idx[0])

        return path, tt


def get_euclidean_distance(x: Cell, y: Cell):
    # distance between two cells
    return math.sqrt((x.row - y.row) ** 2 + (x.col - y.col) ** 2)


def get_distance_utilities(current_cell: Cell, next_cell: Cell):
    if next_cell.state == OBSTACLE:
        return float(sys.maxsize)
    elif next_cell.state == TARGET:
        return 0.0
    elif next_cell.state == PEDESTRIAN:
        return 5.0
    return get_euclidean_distance(current_cell, next_cell)


def add_pedestrian_utilities(ped: Cell):
    for cell in ped.get_pedestrian_grid(R_MAX):
        distance = get_euclidean_distance(ped, cell)
        if distance < R_MAX:
            cell.pedestrian_utility += math.exp(1 / (distance ** 2 - R_MAX ** 2))


def reset_pedestrian_utilities(ped: Cell):
    for cell in ped.get_pedestrian_grid(R_MAX):
        cell.pedestrian_utility = 0
