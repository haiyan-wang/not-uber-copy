import datetime as dt
import heapq
import math



class Node:

    def __init__(self, id: int = None, lat: float = None, lon: float = None) -> None:
        self.id = id
        self.coords = (lat, lon)
        self.neighbors = [] # Edge objects to node neighbors
        self.drivers = [] # Driver objects at node

    def __eq__(self, other) -> bool:
        return self.id == other.id

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
            
            if current_node in distances and current_dist > distances[current_node.id]:
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
        '''

        lat, lon = self.coords
        num_partitions, minlat, maxlat, minlon, maxlon = grid_params
        lat_idx, lon_idx = math.floor( math.ceil(math.sqrt(num_partitions))*(lat - minlat) / (maxlat - minlat) ), math.floor( math.ceil(math.sqrt(num_partitions))*(lon - minlon) / (maxlon - minlon) )
        if lat_idx == 30:
            lat_idx -= 1
        if lon_idx == 30:
            lon_idx -= 1
        grid[lat_idx][lon_idx].append(self)

class Edge:

    def __init__(self, start_node: Node = None, end_node: Node = None, length: float = None, weekday_speeds: dict = None, weekend_speeds: dict = None) -> None:
        self.start_node = start_node
        self.end_node = end_node
        self.length = length
        self.weekday_speeds = weekday_speeds
        self.weekend_speeds = weekend_speeds

    def travel_time(self, start_time: dt.datetime) -> float:
        '''
        Get time to travel over an edge given start time
        '''

        hour = start_time.hour
        if start_time.weekday() > 4:
            return self.weekend_speeds[hour]
        else:
            return self.weekday_speeds[hour]
        
class Driver:

    def __init__(self, id: int = None, timestamp: str = None, lat: float = None, lon: float = None, node: Node = None) -> None:
        self.id = id
        self.time = dt.datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S")
        self.coords = (lat, lon)
        self.node = node

    def __eq__(self, other) -> bool:
        return self.id == other.id
    
    def __lt__(self, other) -> bool:
        return self.time < other.time
    
    def __le__(self, other) -> bool:
        return self.time <= other.time
    
    def __gt__(self, other) -> bool:
        return self.time > other.time
    
    def __ge__(self, other) -> bool:
        return self.time >= other.time

class Passenger:

    def __init__(self, id: int = None, timestamp: str = None, start_lat: float = None, start_lon: float = None, end_lat: float = None, end_lon: float = None, start_node: Node = None, end_node: Node = None) -> None:
        self.id = id
        self.time = dt.datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S")
        self.start_coords = (start_lat, start_lon)
        self.end_coords = (end_lat, end_lon)
        self.start_node = start_node
        self.end_node = end_node

    def __eq__(self, other) -> bool:
        return self.id == other.id
    
    def __lt__(self, other) -> bool:
        return self.time < other.time
    
    def __le__(self, other) -> bool:
        return self.time <= other.time
    
    def __gt__(self, other) -> bool:
        return self.time > other.time
    
    def __ge__(self, other) -> bool:
        return self.time >= other.time
    
    def dist(self, driver: Driver) -> float:
        return math.sqrt((self.start_coords[0] - driver.coords[0])**2 + (self.start_coords[1] - driver.coords[1])**2)

class Ride:

    def __init__(self, start_time: str = None, end_time: str = None, driver: int = None, passenger: int = None, start_lat: float = None, start_lon: float = None, end_lat: float = None, end_lon: float = None) -> None:
        self.start_time = dt.datetime.strptime(start_time, "%m/%d/%Y %H:%M:%S")
        self.end_time = dt.datetime.strptime(end_time, "%m/%d/%Y %H:%M:%S")
        self.driver = driver
        self.passenger = passenger
        self.start_coords = (start_lat, start_lon)
        self.end_coords = (end_lat, end_lon)