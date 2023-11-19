'''
TODO:
    - DIJKSTRA'S TO FIND TIME FOR DRIVER TO PICK UP PASSENGER, THEN DROP OFF (SHOULD WE TAKE INTO ACCOUNT DIFFERENT EDGE TIMES?)
'''




from importlib import reload
import classes
reload(classes)

import os
import json
import csv
from collections import deque
import heapq
import datetime as dt
import random
import math
import time
import concurrent.futures
import multiprocessing



### Data Objects
NODES = {} # <node_id: Node_Object>
NODE_COORDS = {} # <(lat, lon): Node_Object>
DRIVERS = []
PASSENGERS = []

def initialize():

    rootpath = os.path.dirname(os.getcwd())
    
    ### Initialize nodes
    start = time.time()
    with open(rootpath + '/data/node_data.json', 'r') as v:
        n_reader = json.load(v)

    # Generate Node objects
    for node_id in n_reader:
        node = classes.Node(id = node_id, lat = n_reader[node_id]['lat'], lon = n_reader[node_id]['lon'])
        NODES[int(node_id)] = node
        NODE_COORDS[(n_reader[node_id]['lat'], n_reader[node_id]['lon'])] = node
    end = time.time()
    print(f'Nodes initialized, total time {end - start} seconds')

    ### Initialize edges
    start = time.time()
    with open(rootpath + '/data/edges.csv', 'r') as e:
        _ = e.readline()
        e_reader = csv.reader(e)

        # Generate Edge objects
        for edge in e_reader:
            start_node = NODES[int(edge[0])]
            end_node = NODES[int(edge[1])]
            length = edge[2]
            weekday_speeds = dict(zip([*range(0, 24)], edge[3:27]))
            weekend_speeds = dict(zip([*range(0, 24)], edge[27:]))
            neighbor = classes.Edge(start_node, end_node, length, weekday_speeds, weekend_speeds)
            NODES[int(edge[0])].neighbors.append(neighbor) # Add edge to neighbors of start node
    end = time.time()
    print(f'Edges initialized, total time {end - start} seconds')

    ### Initialize drivers
    start = time.time()
    with open(rootpath + '/data/drivers.csv', 'r') as d:
        _ = d.readline()
        d_reader = csv.reader(d)
        
        # Generate Driver objects
        id = 1 # IDs because the data doesn't come with them
        for d in d_reader:
            timestamp, lat, lon = d
            driver = classes.Driver(id = id, timestamp = timestamp, lat = float(lat), lon = float(lon))
            DRIVERS.append(driver)
            id += 1

    # Assign drivers to nearest nodes
    for driver in DRIVERS:
        min_dist = float('inf')
        nearest_node = None
        for node in NODE_COORDS.values():
            dist = driver.euclidean_dist(node)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
        driver.node = nearest_node
    end = time.time()
    print(f'Drivers initialized, total time {end - start} seconds')

    ### Initialize passengers
    start = time.time()
    with open(rootpath + '/data/passengers.csv', 'r') as p:
        _ = p.readline()
        p_reader = csv.reader(p)

        # Generate Passenger objects
        id = 1 # IDs because the data doesn't come with them
        for p in p_reader:
            timestamp, start_lat, start_lon, end_lat, end_lon = p
            passenger = classes.Passenger(id = id, timestamp = timestamp, start_lat = float(start_lat), start_lon = float(start_lon), end_lat = float(end_lat), end_lon = float(end_lon))
            PASSENGERS.append(passenger)
            id += 1

    # Assign passengers to nearest nodes
    for passenger in PASSENGERS:
        min_dist_start = float('inf')
        nearest_node_start = None
        min_dist_end = float('inf')
        nearest_node_end = None
        for node in NODE_COORDS.values():
            start_dist = passenger.euclidean_dist(node)
            if start_dist < min_dist_start:
                min_dist_start = start_dist
                nearest_node_start = node
            end_dist = passenger.euclidean_dist(node, time = 'end')
            if end_dist < min_dist_end:
                min_dist_end = end_dist
                nearest_node_end = node
        passenger.node = nearest_node_start
        passenger.end_node = nearest_node_end
    end = time.time()
    print(f'Passengers initialized, total time {end - start} seconds')

def main():

    init_start = time.time()
    initialize()
    init_end = time.time()
    print(f'Finished initialization, total time {init_end - init_start} seconds')

    #print(PASSENGERS[0].node)
    #print(DRIVERS[0])

if __name__ == '__main__':
    main()