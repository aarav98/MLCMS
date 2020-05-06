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
    """
    Cell represents a unit that a object (PEDESTRIAN, TARGET, OBSTACLE) can occupy in a grid.
    """

    def __init__(self, parent, col, row, state):
        self.system = parent
        self.visited = False
        self.state = state
        self.row = row
        self.col = col
        self.next_cell = None
        # More the utility of a cell, less preferred it is for the next move
        self.distance_utility = float(sys.maxsize)  # Utility representing distance from target
        self.pedestrian_utility = 0.0  # Utility representing penalty depending on distance from a pedestrian

        self.adjacent_cells = []

        self.wait_fmm_penalty = 1
        self.travel_time = 0
        self.initial_predicted_time = 0

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.row == other.row and self.col == other.col and self.state == other.state
        else:
            return False

    def __lt__(self, other):
        return self.distance_utility < other.distance_utility

    def __str__(self):
        return "|(" + str(self.row) + "," + str(self.col) + ")|"

    def set_distance_utility(self, utility: float):
        self.distance_utility = utility

    def get_utility(self):
        return float(self.distance_utility)

    def set_visited(self):
        self.visited = True

    def set_next(self, cell):
        self.next_cell = cell

    def get_adjacent(self):
        """
        Returns a list of all adjacent cells
        :return:
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
        """
        Returns a list all adjacent cells that are not occupied by obstacles
        :return:
        """
        return [cell for cell in self.adjacent_cells if cell not in self.system.obstacles]

    def get_pedestrian_grid(self, r_max):
        """
        Returns a list of cells that lie at most r_max steps away from current cell in all directions
        :param r_max:
        :return:
        """
        ped_grid_cells = []
        for row in self.system.grid[max(0, self.row - r_max): min(self.system.rows, self.row + r_max + 1)]:
            for cell in row[max(0, self.col - r_max):min(self.system.cols, self.col + r_max + 1)]:
                if cell not in self.system.obstacles:
                    ped_grid_cells.append(cell)
        return ped_grid_cells


class System:
    """
    System stores the information about grid of cells
    essentially representing a ground where objects
    (PEDESTRIANS, TARGET, OBSTACLES) can be placed.

    """

    def __init__(self, cols, rows):
        self.initialized = False
        self.rows = rows
        self.cols = cols
        self.grid = [[Cell(self, i, j, EMPTY) for i in range(cols)] for j in range(rows)]
        self.pedestrian = []  # List of cells occupied by pedestrians
        self.target: Cell = None
        self.obstacles = []  # List of cells occupied by obstacles

        self.fmm_distance = np.array([])
        self.tt = np.array([])
        self.pedestrian_fmm = []
        self.dx = 0.4
        self.speed = np.array(np.ones_like(self.grid), dtype=np.double)

        for col in self.grid:
            for cell in col:
                cell.adjacent_cells = cell.get_adjacent()

    def __str__(self):
        for row in self.grid:
            print("\n")
            for cell in row:
                print(str(cell))

    def print_distance_utilities(self):
        """
        Helper method to print distance utilities.
        :return:
        """
        for row in self.grid:
            for cell in row:
                if cell.distance_utility >= sys.maxsize:
                    print(" MAX ", end="  ")
                else:
                    print("{:05.2f}".format(cell.distance_utility), end="  ")
            print()
        print()

    def print_pedestrian_utilities(self):
        """
        Helper method to print pedestrian utilities
        :return:
        """
        for row in self.grid:
            for cell in row:
                if cell.pedestrian_utility >= sys.maxsize:
                    print(" MAX ", end="  ")
                else:
                    print("{:05.2f}".format(cell.pedestrian_utility), end="  ")
            print()
        print()

    def print_utilities(self):
        """
        Helper method to print total utility of a cell
        :return:
        """
        for row in self.grid:
            for cell in row:
                if cell.pedestrian_utility + cell.distance_utility >= sys.maxsize:
                    print(" MAX ", end="  ")
                else:
                    print("{:05.2f}".format(cell.pedestrian_utility + cell.distance_utility), end="  ")
            print()
        print()

    def add_pedestrian_at(self, coordinates: tuple):
        """
        Updates state of the cell to PEDESTRIAN
        :param coordinates:
        :return:
        """
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.pedestrian.append(cell)
        cell.state = PEDESTRIAN

        # Initializing times for FMM implementation to calculate speed of pedestrians
        cell.travel_time = 0
        cell.initial_predicted_time = 0

    def add_pedestrian_fmm(self, coordinates: tuple, speed, travel_time, init_time):
        """

        :param coordinates:
        :param speed:
        :param travel_time:
        :param init_time:
        :return:
        """
        self.add_pedestrian_at(coordinates)
        cell = self.grid[coordinates[0]][coordinates[1]]
        cell.travel_time = travel_time
        cell.initial_predicted_time = init_time
        self.pedestrian_fmm.append(([coordinates[0], coordinates[1]], speed))

    def initialize_speeds(self, speeds=None):
        """
        Initializes speeds for pedestrians if they are provided else sets it to 1.
        :param speeds:
        :return:
        """
        if speeds is None:
            speeds = []
        while len(speeds) < len(self.pedestrian):
            speeds.append(1)
        for pedestrian, speed in zip(self.pedestrian, speeds):
            self.pedestrian_fmm.append(([pedestrian.row, pedestrian.col], speed))

    def remove_pedestrian_at(self, coordinates: tuple):
        """
        Updates state of the cell at given coordinates to EMPTY
        :param coordinates:
        :return:
        """
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.pedestrian.remove(cell)
        cell.state = EMPTY

        cell.travel_time = 0
        cell.initial_predicted_time = 0

    def remove_pedestrian_fmm_at(self, coordinates: tuple, speed):
        """

        :param coordinates:
        :param speed:
        :return:
        """
        self.remove_pedestrian_at(coordinates)
        self.pedestrian_fmm.remove(([coordinates[0], coordinates[1]], speed))

    def add_target_at(self, coordinates: tuple):
        """
        Updates state of the cell at given coordinates to TARGET
        :param coordinates:
        :return:
        """
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.target = cell
        cell.state = TARGET
        return cell

    def add_obstacle_at(self, coordinates: tuple):
        """
        Updates state of the cell at given coordinates to OBSTACLE
        :param coordinates:
        :return:
        """
        cell: Cell = self.grid[coordinates[0]][coordinates[1]]
        self.obstacles.append(cell)
        cell.state = OBSTACLE

    def evaluate_euclidean_cell_utilities(self):
        """
        Calculates euclidean distance of every cell in the system grid from target
        and assigns the value to cell's distance utility
        :return:
        """
        for row in self.grid:
            for cell in row:
                cell.distance_utility = get_euclidean_distance(cell, self.target)

    def update_system_euclidean(self):
        """
        Iteratively computes and assigns next position for each pedestrian cell.
        This only factors in euclidean distance to compute next position to get close to the target,
        but avoids occupying same position as another pedestrian, obstacle or target.
        (This does not guarantee that the pedestrian will reach the target )
        :return:
        """
        next_cells = []
        for cell in self.pedestrian:
            next_cell = cell
            for adjacent in [x for x in cell.adjacent_cells if
                             x != self.target and x not in next_cells + self.pedestrian]:
                if adjacent.distance_utility < next_cell.distance_utility:
                    next_cell = adjacent
            if next_cell.state == OBSTACLE:
                next_cell = cell
            next_cells.append(next_cell)
            cell.set_next(next_cell)

        for cell in self.pedestrian:
            cell.state = EMPTY
            cell.next_cell.state = PEDESTRIAN
        self.pedestrian = next_cells

    def get_next_pedestrian_cells(self):
        """
        Helper method to compute next position.
        Iteratively computes next position for each pedestrian cell.
        This factors in shortest path to the target to compute next position;
        this factors in pedestrian interaction to compute next position
        and avoids occupying same position as another pedestrian, obstacle or target.
        (This guarantees that pedestrian will reach the target)
        :return:
        """
        for ped in self.pedestrian:
            add_pedestrian_utilities(ped)

        next_cells = []
        for ped in self.pedestrian:
            next_cell = ped
            for neighbour in [cell for cell in ped.get_adjacent_minus_obstacles() if
                              cell not in next_cells + self.pedestrian]:
                if neighbour.distance_utility + neighbour.pedestrian_utility <= next_cell.distance_utility + next_cell.pedestrian_utility and neighbour.state != PEDESTRIAN:
                    next_cell = neighbour
                    next_cells.append(next_cell)
            ped.set_next(next_cell)
        for ped in self.pedestrian:
            reset_pedestrian_utilities(ped)

    def update_system_dijikstra(self):
        """
        Updates pedestrian positions to next cells computed by get_next_pedestrian_cells()
        :return:
        """
        new_peds = []
        self.get_next_pedestrian_cells()
        for ped in self.pedestrian:
            if ped.next_cell == self.target:
                continue
            ped.state = EMPTY
            ped.next_cell.state = PEDESTRIAN
            new_peds.append(ped.next_cell)
        self.pedestrian = new_peds

    def evaluate_dijikstra_cell_utilities(self):
        """
        Evaluates and initialises distance utilities for every
        cell using shortest path algorithm (dijikstra).
        :return:
        """
        self.target.set_distance_utility(0)
        unvisited_queue = [(self.target.get_utility(), self.target)]

        while len(unvisited_queue):
            unvisited = heapq.heappop(unvisited_queue)
            current_cell = unvisited[1]
            current_cell.set_visited()
            for next_cell in current_cell.get_adjacent_minus_obstacles():
                if next_cell.visited:
                    continue
                new_dist = current_cell.get_utility() + get_euclidean_distance(current_cell, next_cell)
                if new_dist < next_cell.get_utility():
                    next_cell.set_distance_utility(new_dist)
                    heapq.heappush(unvisited_queue, (next_cell.get_utility(), next_cell))

    def update_system_fmm(self):
        """

        :return:
        """
        ped = [((p[0][0], p[0][1]), p[1]) for p in self.pedestrian_fmm]
        for p in ped:
            path, tt, time = self.calc_fmm(p, self.grid[p[0][0]][p[0][1]].wait_fmm_penalty)
            if self.grid[path[0][0]][path[0][1]].state == PEDESTRIAN:
                # Can be thought of as the level of patience
                self.grid[p[0][0]][p[0][1]].wait_fmm_penalty += 0.001
                print(p, "--> Wait")
                continue
            if self.grid[path[0][0]][path[0][1]] == self.target:
                continue
            init_time = self.grid[p[0][0]][p[0][1]].initial_predicted_time
            speed = p[1]
            time += self.grid[p[0][0]][p[0][1]].travel_time
            self.remove_pedestrian_fmm_at((p[0][0], p[0][1]), speed)
            self.add_pedestrian_fmm(path[0], speed, time, init_time)

        for i in self.pedestrian:
            print((i.row, i.col), '--->', 'Travel Time: ', i.travel_time, ', Predicted Time: ',
                  i.initial_predicted_time)

    def calc_fmm(self, ped, wait=1):
        """

        :param ped:
        :param wait:
        :return:
        """
        p, speed = ped
        if self.fmm_distance.size == 0:
            t_grid = np.array(np.ones_like(self.grid), dtype=np.double)
            mask = np.array(0 * np.ones_like(self.grid), dtype=bool)
            t_grid[self.target.row, self.target.col] = -1
            for i in self.obstacles:
                mask[i.row][i.col] = True
            phi = np.ma.MaskedArray(t_grid, mask)
            self.fmm_distance = skfmm.distance(phi)
            self.grid[p[0]][p[1]].initial_predicted_time = self.fmm_distance[p[0]][p[1]] / self.speed[p[0]][p[1]]
            self.tt = skfmm.travel_time(phi, self.speed, self.dx)
            for z in self.pedestrian_fmm:
                self.grid[z[0][0]][z[0][1]].initial_predicted_time = self.fmm_distance[z[0][0]][z[0][1]] / z[1]
        for i in self.obstacles:
            self.fmm_distance[i.row][i.col] = sys.maxsize
        d = np.copy(self.fmm_distance)
        t = np.copy(self.tt)
        for j in self.pedestrian:
            d[j.row, j.col] *= ((wait * (1 + (1 / (d[j.row, j.col]) * 10))) + 1 / d[j.row, j.col])
        return self.calc_fmm_path(d, t, p, speed)

    def calc_fmm_path(self, distance, t, p, speed):
        """

        :param distance:
        :param t:
        :param p:
        :param speed:
        :return:
        """
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
        time = (get_euclidean_distance(self.grid[p[0]][p[1]], self.grid[path[0][0]][path[0][1]])) / speed
        return path, tt, time


def get_euclidean_distance(x: Cell, y: Cell):
    """
    Returns distance between two cells
    :param x:
    :param y:
    :return:
    """
    return math.sqrt((x.row - y.row) ** 2 + (x.col - y.col) ** 2)


def add_pedestrian_utilities(pedestrian: Cell):
    """
    Computes and adds pedestrian utilities to grid of cells surrounding pedestrian
    at most R_MAX distance away.
    :param pedestrian:
    :return:
    """
    for cell in pedestrian.get_pedestrian_grid(R_MAX):
        distance = get_euclidean_distance(pedestrian, cell)
        if distance < R_MAX:
            cell.pedestrian_utility += math.exp(1 / (distance ** 2 - R_MAX ** 2))


def reset_pedestrian_utilities(pedestrian: Cell):
    """
    Sets pedestrian utilities for the grid of cells surrounding pedestrian
    at most R_MAX distance away to 0.
    :param pedestrian:
    :return:
    """
    for cell in pedestrian.get_pedestrian_grid(R_MAX):
        cell.pedestrian_utility = 0
