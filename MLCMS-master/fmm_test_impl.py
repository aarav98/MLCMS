''''
class fmm:
    #params: system -> grid style layout with pedestrians/obstacles and targets.

    def __init__(self, system):
        self.t_grid = [[(sys.maxsize) for i in range(system.rows)] for j in range(system.cols)]
        self.neighbor = []
        self.known = []
        self.system = system
        self.far = [(j.row, j.col) for i in self.grid for j in i]
        self.heap_neighbor = []                                     #heap for storing the neighbors and their calculated time in a tuple
        self.known_values = []                                       #list containing coords of which the time is already calulated


    def far_to_neighbor(self, coord):
        #to take an element in the 'FAR' list to the 'NEIGHBOR' list
        #param: a tuple consisting of a pair of co-ordinates

        if coord in self.far:
            self.neighbor.append(self.far.pop(self.far.index(coord)))
            self.system.grid[coord[0]][coord[1]].fmm_state = 0

        else:
            print("Incorrect format/Tuple doesnt exist in 'FAR'")


    def neighbor_to_known(self, coord):
        #to take an element in the 'NEIGHBOR' list to the 'KNOWN' list.
        #param: a tuple consisting of a pair of co-ordinates

        if coord in self.neighbor:
            self.known.append(self.neighbor.pop(self.neighbor.index(coord)))
            self.system.grid[coord[0]][coord[1]].fmm_state = 1

        else:
            print("Incorrect format/Tuple doesnt exist in 'NEIGHBOR'")


    def add_time(self, time, coord):
        #adds a time to the t_grid matrix.
        #param: time -> time to be added, coord -> tuple of coordinates of the the point
        self.t_grid[coord[0]][coord[1]] = time
        
    
    def calc_time(self, cell):
        #implement this function
        #calculates the time take to go to the next cell
        #returns calculated time for a cell c
        #param: cell -> type(cell) for which the time is to be calculated.

        c = (cell.row, cell.col)
        t1 = max(self.t_grid[c[0]][c[1]] - self.t_grid[c[0] - 1][c[1]], self.t_grid[c[0]][c[1]] - self.t_grid[c[0] + 1][c[1]], 0)
        t2 = max(self.t_grid[c[0]][c[1]] - self.t_grid[c[0]][c[1] - 1], self.t_grid[c[0]][c[1]] - self.t_grid[c[0]][c[1] + 1], 0)

        z = (((t1 ** 2) + (t2 ** 2)) ** 0.5)
        if z != 0:
            t = 1/z
        else:
            t = 0

        a = min(self.t_grid[c[0] - 1][c[1]], self.t_grid[c[0] + 1][c[1]])
        b = min(self.t_grid[c[0]][c[1] - 1], self.t_grid[c[0]][c[1] + 1])

        #Solving the quadratic equation
        T = None
        if t > abs(a-b):
            T = (a+b+(2*(t**2) - (a-b)**2)**0.5)/2
        else:
            T = t**2 + min(a, b)

        #print((T, c))

        return (T, c)

    
    def insert_heap(self, data):
        #param: data - > tuple consisting of time, coordinates in a tuple. eg: (2, (2,25))
        #used to insert data to the heap
        heapq.heappush(self.heap_neighbor, data)

    def delete_heap(self, data):
        #param: data - > tuple consisting of time, coordinates in a tuple. eg: (2, (2,25))
        #used to delete and element from the heap while keeping the heap structure
        temp = list()
        while self.heap_neighbor:
            temp.append(heapq.heappop(self.heap_neighbor))
        temp.remove(data)
        heapq.heapify(temp)
        self.heap_neighbor = temp


    def check_double(self, data):
        #checks if the data is present in the heap or not. if it is, then the value which is lower will be kept.
        #param: data -> tuple with time as the first element and a tuple of coord as the second. eg: (2, (2, 25))
        temp = list()
        while self.heap_neighbor:
            temp.append(heapq.heappop(self.heap_neighbor))
        temp1 = [i[1] for i in temp]
        if data[1] in temp1:
            ind = temp1.index(data[1])
            if temp[ind][0] > data[0]:
                self.delete_heap(temp[ind])
                self.insert_heap(data)
                self.add_time(data[0], data[1])
            else:
                return
        else:
            heapq.heappush(self.heap_neighbor,data)


    def find_values(self, pedestrian):
        
        #param: pedestrian -> list of cells, the starting points/pedestrians.

        for ped in pedestrian:
            cell = self.system.grid[ped[0]][ped[0]]
            row = cell.row
            col = cell.col

            #set the time for the start point to 0
            self.t_grid[row][col] = 0

            #put the the start point in the known list
            self.known.append((row, col))

            #get the target
            target = self.system.target

            while target not in self.known:
                
                it = 0
                
                new_neighbors = [i for i in get_adjacent(cell, self.system) if i not in self.known_values and i not in self.neighbor]
                self.neighbor.extend(new_neighbors)
                for z in new_neighbors:
                    #print(it)
                    z.fmm_state=0
                    it+=1
                    time = self.calc_time(z)         #time -> (time, (coord)) -> (2, (2, 25))
                    self.check_double(time)
                
                cell = self.system.grid[time[1][0]][time[1][1]]
                smallest_in_heap = heapq.heappop(self.heap_neighbor)
                self.known.append(smallest_in_heap)
                self.known_values.append(self.system.grid[smallest_in_heap[1][0]][smallest_in_heap[1][1]])
                print(smallest_in_heap)
                

        def print_tt():
            #prints travel time values
            print("reached here!")
            for i in range(self.system.rows):
                for j in range(self.system.cols):
                    print(self.t_grid[i][j],end='\t')
                print()

    '''
