import datetime as dt
import heapq
import math



class NotUberObject:

    def __init__(self, id: int = None, lat: float = None, lon: float = None) -> None:
        self.id = id
        self.coords = (lat, lon)

        self.node = None

    def __eq__(self, other) -> bool:
        return isinstance(self, NotUberObject) and isinstance(other, NotUberObject) and self.id == other.id
    
    def __hash__(self) -> int:
        return self.id # This is a really bad hashcode but its fine since we're only ever hashing objects of the same type

    def euclidean_dist(self, other, *args, **kwargs) -> float:
        '''
        Return distance between latitude/longitude coordinates
            - Object must have coords attribute
        '''

        if not self.coords or not other.coords:
            print('Missing latitude/longitude coordinates')
            return
        
        return math.sqrt((self.coords[0] - other.coords[0])**2 + (self.coords[1] - other.coords[1])**2)

    def network_dist(self, other, time) -> float:
        '''
        Return length/time of shortest path through network 
            - Object must have node attribute
            - Call on object that is actually travelling (i.e. driver.network_dist(passenger, driver.time))
        '''

        if not self.node or not other.node:
            print('Objects not on network')
            return 
        
        if not self.time:
            print('No time specified')
            return
        
        return self.node.shortest_path(end_node = other.node, start_time = time)

class Node(NotUberObject):

    def __init__(self, id: int = None, lat: float = None, lon: float = None) -> None:
        super().__init__(id, lat, lon)

        self.neighbors = [] # Edge objects to node neighbors
        self.drivers = [] # Driver objects at node

    def __eq__(self, other) -> bool:
        return isinstance(self, Node) and isinstance(other, Node) and self.id == other.id

    def shortest_path(self, end_node, start_time: dt.datetime) -> float:
        '''
        Dijkstra's Algorithm to find shortest travel time between two nodes

        Returns -1 if no path is found
        '''

        distances = {}
        distances[self.id] = 0
        pq = [(0, self)]

        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_node == end_node:
                return current_dist
            
            if current_node.id in distances and current_dist > distances[current_node.id]:
                continue
            
            for edge in current_node.neighbors:
                neighbor = edge.end_node
                new_dist = current_dist + edge.travel_time(start_time) # Heuristic - finding path with shortest time to destination at start time (without accounting for changes during travel)
                if neighbor.id not in distances or new_dist < distances[neighbor.id]:
                    distances[neighbor.id] = new_dist
                    heapq.heappush(pq, (new_dist, neighbor))
                    
        return -1
    
    def partition(self, grid: list = None, grid_params: list = None) -> None:
        '''
        Partition node into grid
            - grid: m x m matrix of lists representing subpartitions (WILL BE MUTATED)
            - grid_params: [num_partitions, minlat, maxlat, minlon, maxlon]

        grid and grid_params are global variables in each file that are set by the initialize function
        '''

        lat, lon = self.coords
        num_partitions, minlat, maxlat, minlon, maxlon = grid_params
        lat_idx, lon_idx = math.floor( math.ceil(math.sqrt(num_partitions))*(lat - minlat) / (maxlat - minlat) ), math.floor( math.ceil(math.sqrt(num_partitions))*(lon - minlon) / (maxlon - minlon) ) # Index of subpartition in grid
        
        # Edge cases
        if lat_idx == 30:
            lat_idx -= 1 
        if lon_idx == 30:
            lon_idx -= 1

        grid[lat_idx][lon_idx].append(self) # Add node to appropriate subpartition
        
class Person(NotUberObject):

    def __init__(self, id: int = None, timestamp: str = None, lat: float = None, lon: float = None) -> None:
        super().__init__(id, lat, lon)
        self.time = dt.datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S")

    def __eq__(self, other) -> bool:
        return isinstance(self, Person) and isinstance(other, Person) and self.id == other.id

    def __lt__(self, other) -> bool:
        return self.time < other.time
    
    def __le__(self, other) -> bool:
        return self.time <= other.time
    
    def __gt__(self, other) -> bool:
        return self.time > other.time
    
    def __ge__(self, other) -> bool:
        return self.time >= other.time

    def partition(self, coords: tuple = None, grid_params: list = None) -> tuple:
        '''
        Find subpartition of Person
            - coods: Lat/lon coordinates of object to be partitioned
            - grid_params: [num_partitions, minlat, maxlat, minlon, maxlon]
        '''

        lat, lon = coords
        num_partitions, minlat, maxlat, minlon, maxlon = grid_params
        lat_idx, lon_idx = math.floor( math.ceil(math.sqrt(num_partitions))*(lat - minlat) / (maxlat - minlat) ), math.floor( math.ceil(math.sqrt(num_partitions))*(lon - minlon) / (maxlon - minlon) )

        # Edge cases
        if lat_idx >= 30:
            lat_idx = 29
        elif lat_idx < 0:
            lat_idx = 0
        if lon_idx >= 30:
            lon_idx = 29
        elif lon_idx < 0:
            lon_idx = 0

        # Index of subpartition in grid matrix
        return (lat_idx, lon_idx)
    
    def assign_node(self, coords: tuple = None, grid: list = None, grid_params: list = None) -> Node:
        '''
        Assign Person to nearest node given coordinates and partition grid
            - - coods: Lat/lon coordinates of object to be partitioned
            - grid: nodes in graph grouped by subpartition
            - grid_params: [num_partitions, minlat, maxlat, minlon, maxlon]
        '''

        lat_idx, lon_idx = self.partition(coords, grid_params) # Get subpartition of object

        # Get surrounding subpartitions (max 3x3 grid surrounding subpartition)
        surrounding_grid = []
        for i in range(-1, 1):
            for j in range(-1, 1):
                surrounding_grid.append((abs(lat_idx+i), abs(lon_idx+j)))
        search_space = list(set(surrounding_grid))

        # Get all nodes in search space
        nodes = []
        for idx1, idx2 in search_space:
            nodes.extend(grid[idx1][idx2])

        # Find nearest node
        nearest_node = None
        min_dist = float('inf')
        for node in nodes:
            if math.sqrt((self.coords[0] - node.coords[0])**2 + (self.coords[1] - node.coords[1])**2) < min_dist:
                nearest_node = node
                min_dist = math.sqrt((self.coords[0] - node.coords[0])**2 + (self.coords[1] - node.coords[1])**2)

        return nearest_node

class Driver(Person):

    def __init__(self, id: int = None, timestamp: str = None, lat: float = None, lon: float = None) -> None:
        super().__init__(id, timestamp, lat, lon)

    def __eq__(self, other) -> bool:
        return isinstance(self, Driver) and isinstance(other, Driver) and self.id == other.id

class Passenger(Person):

    def __init__(self, id: int = None, timestamp: str = None, start_lat: float = None, start_lon: float = None, end_lat: float = None, end_lon: float = None, start_node: Node = None, end_node: Node = None) -> None:
        super().__init__(id, timestamp, start_lat, start_lon)
        self.end_coords = (end_lat, end_lon)

        self.end_node = None 

    def __eq__(self, other) -> bool:
        return isinstance(self, Passenger) and isinstance(other, Passenger) and self.id == other.id

    def euclidean_dist(self, other, time = 'start') -> float:
        '''
        Return distance between latitude/longitude coordinates
            - Object must have coords attribute
            - time: {'start', 'end'} specifies whether you want the distance to/from the passenger's start location or end location
        '''

        if not self.coords or not other.coords:
            print('Missing latitude/longitude coordinates')
            return
        
        if time == 'start':
            return math.sqrt((self.coords[0] - other.coords[0])**2 + (self.coords[1] - other.coords[1])**2)
        if time == 'end':
            return math.sqrt((self.end_coords[0] - other.coords[0])**2 + (self.end_coords[1] - other.coords[1])**2)

class Edge:

    def __init__(self, start_node: Node = None, end_node: Node = None, length: float = None, weekday_speeds: dict = None, weekend_speeds: dict = None) -> None:
        self.start_node = start_node
        self.end_node = end_node
        self.length = float(length)
        self.weekday_speeds = weekday_speeds
        self.weekend_speeds = weekend_speeds

    def travel_time(self, start_time: dt.datetime) -> float:
        '''
        Get time to travel over an edge given start time
        '''

        hour = start_time.hour
        if start_time.weekday() > 4:
            return 60*self.length / float(self.weekend_speeds[hour])
        else:
            return 60*self.length / float(self.weekday_speeds[hour])
        
'''
class Ride:

    def __init__(self, start_time: str = None, end_time: str = None, driver: int = None, passenger: int = None, start_lat: float = None, start_lon: float = None, end_lat: float = None, end_lon: float = None) -> None:
        self.start_time = dt.datetime.strptime(start_time, "%m/%d/%Y %H:%M:%S")
        self.end_time = dt.datetime.strptime(end_time, "%m/%d/%Y %H:%M:%S")
        self.driver = driver
        self.passenger = passenger
        self.start_coords = (start_lat, start_lon)
        self.end_coords = (end_lat, end_lon)
'''