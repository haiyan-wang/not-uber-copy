import json
import csv
import datetime as dt
import time
import heapq


### Classes

class Edge:

    def __init__(self, start_node_id: int = None, end_node_id: int = None, day_type: str = None, hour: int = None, length: int = None, max_speed: float = None, time: float = None) -> None:
        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        self.day_type = day_type
        self.hour = hour
        self.length = length
        self.max_speed = max_speed
        self.time = time

class Node:

    def __init__(self, id: int = None, lat: float = None, lon: float = None) -> None:
        self.id = id
        self.lat = lat
        self.lon = lon
        self.neighbors = {} # {end_node_id: Edge}
        self.drivers = []

    def shortest_path(self, end_node):
        distances = {}
        distances[self.id] = 0
        pq = [(0, self)]
        while pq:
            (dist, current_node) = heapq.heappop(pq)
            
            if current_node.id == end_node.id:
                return dist
            
            if current_node in distances and dist > distances[current_node.id]:
                continue
            
            for edge_id, edge in current_node.neighbors.items():
                neighbor = nodes[edge.end_node_id]
                distance = dist + edge.time
                if neighbor.id not in distances or distance < distances[neighbor.id]:
                    distances[neighbor.id] = distance
                    heapq.heappush(pq, (distance, neighbor))
        return distances

class Driver:

    def __init__(self, timestamp: str = None, lat: float = None, lon: float = None) -> None:
        self.time = time.mktime(dt.datetime.strptime(timestamp, date_format).timetuple())
        self.lat = lat
        self.lon = lon

class Passenger:

    def __init__(self, timestamp: str = None, s_lat: float = None, s_lon: float = None, e_lat: float = None, e_lon: float = None) -> None:
        self.time = time.mktime(dt.datetime.strptime(timestamp, date_format).timetuple())
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

### Graph Construction

with open('adjacency.json', 'r') as g:
    adjList = json.load(g)

with open('node_data.json', 'r') as n:
    nodeList = json.load(n)

nodes = {}
for node_id in nodeList:
    nodes[int(node_id)] = Node(id = node_id, lat = nodeList[node_id]['lat'], lon = nodeList[node_id]['lon'])

for start_node in adjList:
    node = nodes[int(start_node)]
    for end_node in adjList[start_node]:
        node.neighbors[int(end_node)] = Edge(start_node_id = start_node, end_node_id = end_node, **adjList[start_node][end_node])

### Reading Drivers and Passengers

date_format = "%m/%d/%Y %H:%M:%S"

drivers = []
with open('drivers.csv', 'r') as d:
    _ = d.readline()
    d_reader = csv.reader(d)
    for d in d_reader:
        drivers.append(Driver(*d))

passengers = []
with open('passengers.csv', 'r') as p:
    _ = p.readline()
    p_reader = csv.reader(p)
    for p in p_reader:
        passengers.append(Passenger(*p))
