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



### Data Objects
NODES = {} # <node_id: Node_Object>
NODE_COORDS = {} # <(lat, lon): Node_Object>
DRIVERS = []
PASSENGERS = []

### Grid Params
PARTITIONS = 900
MINLAT, MINLON, MAXLAT, MAXLON = float('inf'), float('inf'), float('-inf'), float('-inf') # Getting edges for grid partitioning
GRID = [[[] for i in range(math.ceil(math.sqrt(PARTITIONS)))] for j in range(math.ceil(math.sqrt(PARTITIONS)))]
GRID_PARAMS = []

def initialize():

    rootpath = os.path.dirname(os.getcwd())
    
    ### Initialize nodes
    with open(rootpath + '/data/node_data.json', 'r') as v:
        n_reader = json.load(v)

    # Generate Node objects
    for node_id in n_reader:
        node = classes.Node(id = node_id, lat = n_reader[node_id]['lat'], lon = n_reader[node_id]['lon'])
        NODES[int(node_id)] = node
        NODE_COORDS[(n_reader[node_id]['lat'], n_reader[node_id]['lon'])] = node

        # Get edges of grid
        global MINLAT, MINLON, MAXLAT, MAXLON
        if n_reader[node_id]['lat'] < MINLAT:
            MINLAT = n_reader[node_id]['lat']
        if n_reader[node_id]['lon'] < MINLON:
            MINLON = n_reader[node_id]['lon']
        if n_reader[node_id]['lat'] > MAXLAT:
            MAXLAT = n_reader[node_id]['lat']
        if n_reader[node_id]['lon'] > MAXLON:
            MAXLON = n_reader[node_id]['lon']
    
    # Set grid params
    global GRID_PARAMS
    GRID_PARAMS.extend([PARTITIONS, MINLAT, MAXLAT, MINLON, MAXLON])
    for node in NODES.values():
        node.partition(GRID, GRID_PARAMS)

    ### Initialize edges
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

    ### Initialize drivers
    with open(rootpath + '/data/drivers.csv', 'r') as d:
        _ = d.readline()
        d_reader = csv.reader(d)
        
        # Generate Driver objects
        id = 1 # IDs because the data doesn't come with them
        for d in d_reader:
            time, lat, lon = d
            driver = classes.Driver(id = id, timestamp = time, lat = float(lat), lon = float(lon))
            driver.node = driver.assign_node(driver.coords, GRID, GRID_PARAMS) # Assign driver to nearest node
            DRIVERS.append(driver)
            id += 1

    ### Initialize passengers
    with open(rootpath + '/data/passengers.csv', 'r') as p:
        _ = p.readline()
        p_reader = csv.reader(p)

        # Generate Passenger objects
        id = 1 # IDs because the data doesn't come with them
        for p in p_reader:
            time, start_lat, start_lon, end_lat, end_lon = p
            passenger = classes.Passenger(id = id, timestamp = time, start_lat = float(start_lat), start_lon = float(start_lon), end_lat = float(end_lat), end_lon = float(end_lon))
            passenger.start_node = passenger.assign_node(passenger.coords, GRID, GRID_PARAMS)
            passenger.end = passenger.assign_node(passenger.end_coords, GRID, GRID_PARAMS)
            PASSENGERS.append(passenger)
            id += 1

def main():

    initialize()

    passenger_wait_times, driver_idle_times = [], [] # Metrics

    driver_queue = [] # Priority queue for driver by available time
    for driver in DRIVERS:
        heapq.heappush(driver_queue, (driver, driver.time))
    passenger_queue = deque(PASSENGERS) # Priority queue for passenger by ride request time (already sorted and no pushes so we use deque)

    while passenger_queue:

        available_drivers = [] # Available drivers when passenger makes request

        # Match passenger and driver
        passenger = passenger_queue.popleft() # Current passenger request
        try: # Drivers available
            if driver_queue[0][0].time > passenger.time: # If no available drivers
                driver, _ = heapq.heappop(driver_queue)
                available_drivers.append(driver)
            else:
                while driver_queue and driver_queue[0][0].time <= passenger.time: # Get all available drivers at current time
                    driver, _ = heapq.heappop(driver_queue)
                    available_drivers.append(driver)
        except:
            print(f'No more drivers available. Remaining passengers: {len(passenger_queue)}')
            print(f'Average Passenger Wait Time: {sum(passenger_wait_times) / len(passenger_wait_times)}')
            print(f'Average Driver Idle Time: {sum(driver_idle_times) / len(driver_idle_times)}')
            return
        
        # Get closest driver
        min_dist = float('inf')
        assigned_driver = None
        for driver in available_drivers:
            if passenger.euclidean_dist(driver) < min_dist:
                assigned_driver = driver

        # Check wait times (in minutes)
        passenger_wait_time = 0
        driver_idle_time = 0
        if assigned_driver.time < passenger.time: # Driver ready before passenger
            wait = passenger.time - driver.time
            driver_idle_time += wait.total_seconds() / 60
        elif assigned_driver.time > passenger.time: # Passenger ready before driver
            wait = assigned_driver.time - passenger.time
            passenger_wait_time += wait.total_seconds() / 60
        passenger_wait_times.append(passenger_wait_time)
        driver_idle_times.append(driver_idle_time)

        assigned_driver.time += dt.timedelta(minutes = 10)
        
        p = random.randint(1, 15)
        for driver in available_drivers:
            if driver == assigned_driver:
                if p > 1: # Geometric random variable, expect every driver to do 10 rides per night
                    heapq.heappush(driver_queue, (driver, driver.time))
                    continue        
            heapq.heappush(driver_queue, (driver, driver.time))
    
    print(f'Average Passenger Wait Time: {sum(passenger_wait_times) / len(passenger_wait_times)}')
    print(f'Average Driver Idle Time: {sum(driver_idle_times) / len(driver_idle_times)}')

if __name__ == '__main__':
    main()