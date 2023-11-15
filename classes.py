import datetime as dt
import time
import heapq

class Node:

    def __init__(self, id: int = None, lat: float = None, lon: float = None) -> None:
        self.id = id
        self.coords = (lat, lon)
        self.neighbors = [] # Edge objects
        self.drivers = [] # Driver objects

    def __eq__(self, other):
        return self.id == other.id

    def shortest_path(self, end_node, start_time: dt.datetime):
        '''
        Dijkstra's Algorithm to find shortest travel time between two nodes
        '''

        distances = {}
        distances[self.id] = 0
        pq = [(0, self)]
        while pq:
            dist, current_node = heapq.heappop(pq)
            
            if current_node == end_node:
                return dist
            
            if current_node in distances and dist > distances[current_node.id]:
                continue
            
            for edge in current_node.neighbors:
                neighbor = edge.end_node
                distance = dist + edge.travel_time(start_time)
                if neighbor.id not in distances or distance < distances[neighbor.id]:
                    distances[neighbor.id] = distance
                    heapq.heappush(pq, (distance, neighbor))
                    
        return distances

class Edge:

    def __init__(self, start_node: Node = None, end_node: Node = None, length: float = None, weekday_speeds: dict = None, weekend_speeds: dict = None) -> None:
        self.start_node = start_node
        self.end_node = end_node
        self.length = length
        self.weekday_speeds = weekday_speeds
        self.weekend_speeds = weekend_speeds

    def travel_time(self, start_time: dt.datetime):
        '''
        Get time to travel over an edge given start time
        '''

        hour = start_time.hour
        if start_time.weekday() > 4:
            return self.weekend_speeds[hour]
        else:
            return self.weekday_speeds[hour]

class Driver:

    def __init__(self, timestamp: str = None, lat: float = None, lon: float = None) -> None:
        self.time = time.mktime(dt.datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S").timetuple())
        self.lat = lat
        self.lon = lon

class Passenger:

    def __init__(self, timestamp: str = None, s_lat: float = None, s_lon: float = None, e_lat: float = None, e_lon: float = None) -> None:
        self.time = dt.datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S")
        self.start_lat = s_lat
        self.start_lon = s_lon
        self.end_lat = e_lat
        self.end_lon = e_lon

class Ride:

    def __init__(self, start_time: str = None, end_time: str = None, driver: int = None, passenger: int = None, start_lat: float = None, start_lon: float = None, end_lat: float = None, end_lon: float = None) -> None:
        self.start_time = start_time # convert to dt.datetime obj
        self.end_time = end_time # convert to dt.datetime obj
        self.driver = driver
        self.passenger = passenger
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.end_lat = end_lat
        self.end_lon = end_lon