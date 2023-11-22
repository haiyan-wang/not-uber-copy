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
import time
import multiprocessing
import math

### Data Objects
NODES = {} # <node_id: Node_Object>
NODE_COORDS = {} # <(lat, lon): Node_Object>
DRIVERS = []
PASSENGERS = []

### Preprocessed information about network
AVG_MPH = 0
NUM_ROADS = 0

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

            # Network data (preprocessing)
            avg_speed = 0
            for _, val in weekday_speeds.items():
                avg_speed += float(val)
            for _, val in weekend_speeds.items():
                avg_speed += float(val)
            avg_speed /= len(weekday_speeds) + len(weekend_speeds)
            
            global AVG_MPH
            global NUM_ROADS
            AVG_MPH += avg_speed
            NUM_ROADS += 1

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
            passenger.node = passenger.assign_node(passenger.coords, GRID, GRID_PARAMS)
            passenger.end_node = passenger.assign_node(passenger.end_coords, GRID, GRID_PARAMS)
            PASSENGERS.append(passenger)
            id += 1

    ### Average MPH on network
    AVG_MPH /= NUM_ROADS
    print(f'Average MPH: {AVG_MPH}')

# from importlib import reload
# import classes
# reload(classes)

# import os
# import json
# import csv
# from collections import deque
# import heapq
# import datetime as dt
# import random
# import time
# import multiprocessing



# ### Data Objects
# NODES = {} # <node_id: Node_Object>
# DRIVERS = []
# PASSENGERS = []

# def initialize():

#     rootpath = os.path.dirname(os.getcwd())

#     ### Initialize nodes
#     with open(rootpath + '/data/node_data.json', 'r') as v:
#         n_reader = json.load(v)

#     # Generate Node objects
#     for node_id in n_reader:
#         node = classes.Node(id = node_id, lat = n_reader[node_id]['lat'], lon = n_reader[node_id]['lon'])
#         NODES[int(node_id)] = node
#     print('Nodes initialized')
    
#     ### Initialize edges
#     with open(rootpath + '/data/edges.csv', 'r') as e:
#         _ = e.readline()
#         e_reader = csv.reader(e)

#         # Generate Edge objects
#         for edge in e_reader:
#             start_node = NODES[int(edge[0])]
#             end_node = NODES[int(edge[1])]
#             length = edge[2]
#             weekday_speeds = dict(zip([*range(0, 24)], edge[3:27]))
#             weekend_speeds = dict(zip([*range(0, 24)], edge[27:]))
#             neighbor = classes.Edge(start_node, end_node, length, weekday_speeds, weekend_speeds)
#             NODES[int(edge[0])].neighbors.append(neighbor) # Add edge to neighbors of start node
#     print('Edges initialized')

#     ### Initialize drivers
#     with open(rootpath + '/data/drivers.csv', 'r') as d:
#         _ = d.readline()
#         d_reader = csv.reader(d)
        
#         # Generate Driver objects
#         id = 1 # IDs because the data doesn't come with them
#         for d in d_reader:
#             timestamp, lat, lon = d
#             driver = classes.Driver(id = id, timestamp = timestamp, lat = float(lat), lon = float(lon))
#             DRIVERS.append(driver)
#             id += 1

#     # Assign drivers to nearest nodes
#     for driver in DRIVERS:
#         min_dist = float('inf')
#         nearest_node = None
#         for node in NODES.values():
#             dist = driver.euclidean_dist(node)
#             if dist < min_dist:
#                 min_dist = dist
#                 nearest_node = node
#         driver.node = nearest_node
#     print('Drivers initialized')

#     ### Initialize passengers
#     with open(rootpath + '/data/passengers.csv', 'r') as p:
#         _ = p.readline()
#         p_reader = csv.reader(p)

#         # Generate Passenger objects
#         id = 1 # IDs because the data doesn't come with them
#         for p in p_reader:
#             timestamp, start_lat, start_lon, end_lat, end_lon = p
#             passenger = classes.Passenger(id = id, timestamp = timestamp, start_lat = float(start_lat), start_lon = float(start_lon), end_lat = float(end_lat), end_lon = float(end_lon))
#             PASSENGERS.append(passenger)
#             id += 1

#     # Assign passengers to nearest nodes
#     for passenger in PASSENGERS:
#         min_dist_start = float('inf')
#         nearest_node_start = None
#         min_dist_end = float('inf')
#         nearest_node_end = None
#         for node in NODES.values():
#             start_dist = passenger.euclidean_dist(node)
#             if start_dist < min_dist_start:
#                 min_dist_start = start_dist
#                 nearest_node_start = node
#             end_dist = passenger.euclidean_dist(node, time = 'end')
#             if end_dist < min_dist_end:
#                 min_dist_end = end_dist
#                 nearest_node_end = node
#         passenger.node = nearest_node_start
#         passenger.end_node = nearest_node_end
#     print('Passengers initialized')

def main():

    init_start = time.time()
    initialize()
    init_end = time.time()
    print(f'Finished initialization, total time {init_end - init_start} seconds')

    # Metrics
    passenger_wait_times, driver_idle_times = [], [] 
    total_ride_profit = 0

    driver_queue = [] # Priority queue for driver by available time
    for driver in DRIVERS:
        heapq.heappush(driver_queue, (driver, driver.time))
    passenger_queue = deque(PASSENGERS) # Priority queue for passenger by ride request time (already sorted and no pushes so we use deque)

    while passenger_queue:
        print(len(passenger_queue))

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
            print(f'No more drivers available. Remaining passengers: {len(passenger_queue)} minutes')
            print(f'Average Passenger Wait Time: {sum(passenger_wait_times) / len(passenger_wait_times)} minutes')
            print(f'Average Driver Idle Time: {sum(driver_idle_times) / len(driver_idle_times)} minutes')
            print(f'Average Driver Profit: {total_ride_profit / len(DRIVERS)} minutes')
            return
        
        # Get closest driver
        min_dist = float('inf')
        assigned_driver = None
        for driver in available_drivers:
            dist = driver.node.shortest_path(passenger.node, passenger.time) # Closest point along network
            if dist < min_dist:
                assigned_driver = driver
                min_dist = dist

        # Wait times for driver assignment (in minutes)
        passenger_wait_time = 0
        driver_idle_time = 0
        if assigned_driver.time < passenger.time: # Driver ready before passenger
            wait = passenger.time - assigned_driver.time
            driver_idle_time += wait.total_seconds() / 60
        elif assigned_driver.time > passenger.time: # Passenger ready before driver
            wait = assigned_driver.time - passenger.time
            passenger_wait_time += wait.total_seconds() / 60

        # Wait time for driver to arrive
        approx_arrival_time = min_dist # Time taken for driver to arrive to passenger
        assigned_driver.node = passenger.node # Driver arrives at passenger's location
        passenger.time += dt.timedelta(minutes = approx_arrival_time) # Time at driver's arrival
        assigned_driver.time += dt.timedelta(minutes = approx_arrival_time) # Time at driver's arrival
        
        # Driving time
        approx_drive_time = assigned_driver.node.shortest_path(passenger.end_node, passenger.time)  # Time taken for driver to drop off passenger
        assigned_driver.node = passenger.end_node # Driver drops passenger off
        assigned_driver.time += dt.timedelta(minutes = approx_drive_time) # Time at driver's arrival
        
        # Metrics
        total_ride_profit += approx_drive_time - approx_arrival_time
        passenger_wait_time += approx_arrival_time + approx_drive_time
        passenger_wait_times.append(passenger_wait_time)
        driver_idle_times.append(driver_idle_time)
        
        # Add drivers back to queue, simulating potential driver drop out
        p = random.randint(1, 15)
        for driver in available_drivers:
            if driver == assigned_driver:
                if p > 1: # Geometric random variable, expect every driver to do 15 rides per night
                    heapq.heappush(driver_queue, (driver, driver.time))
                    continue        
            heapq.heappush(driver_queue, (driver, driver.time))
    
    print(f'Average Passenger Wait Time: {sum(passenger_wait_times) / len(passenger_wait_times)} minutes')
    print(f'Average Driver Idle Time: {sum(driver_idle_times) / len(driver_idle_times)} minutes')
    print(f'Total Driver Profit: {total_ride_profit} minutes')
    print(f'Average Driver Profit: {total_ride_profit / len(DRIVERS)} minutes')

if __name__ == '__main__':
    START = time.time() # Timing simulation
    main()
    END = time.time() # Timing simulation
    print(f'Simulation Runtime: {END - START} seconds')