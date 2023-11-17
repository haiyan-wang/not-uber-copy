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


NODES = {} # <node_id: Node_Object>
NODE_COORDS = {} # <(lat, lon): Node_Object>
DRIVERS = []
PASSENGERS = []

def initialize():

    rootpath = os.path.dirname(os.getcwd())
    
    ### Initialize nodes
    with open(rootpath + '/data/node_data.json', 'r') as v:
        n_reader = json.load(v)
    for node_id in n_reader:
        node = classes.Node(id = node_id, lat = n_reader[node_id]['lat'], lon = n_reader[node_id]['lon'])
        NODES[int(node_id)] = node
        NODE_COORDS[(n_reader[node_id]['lat'], n_reader[node_id]['lon'])] = node

    ### Initialize edges
    with open(rootpath + '/data/edges.csv', 'r') as e:
        _ = e.readline()
        e_reader = csv.reader(e)
        for edge in e_reader:
            start_node = NODES[int(edge[0])]
            end_node = NODES[int(edge[1])]
            length = edge[2]
            weekday_speeds = dict(zip([*range(0, 24)], edge[3:27]))
            weekend_speeds = dict(zip([*range(0, 24)], edge[27:]))
            neighbor = classes.Edge(start_node, end_node, length, weekday_speeds, weekend_speeds)
            NODES[int(edge[0])].neighbors.append(neighbor)

    ### Initialize drivers
    with open(rootpath + '/data/drivers.csv', 'r') as d:
        _ = d.readline()
        d_reader = csv.reader(d)
        id = 1
        for d in d_reader:
            time, lat, lon = d
            #DRIVERS.append(classes.Driver(id = id, timestamp = time, lat = float(lat), lon = float(lon), node = NODE_COORDS[(float(lat), float(lon))]))
            DRIVERS.append(classes.Driver(id = id, timestamp = time, lat = float(lat), lon = float(lon)))
            id += 1

    ### Initialize passengers
    with open(rootpath + '/data/passengers.csv', 'r') as p:
        _ = p.readline()
        p_reader = csv.reader(p)
        id = 1
        for p in p_reader:
            time, start_lat, start_lon, end_lat, end_lon = p
            #PASSENGERS.append(classes.Passenger(id = id, timestamp = time, start_lat = float(start_lat), start_lon = float(start_lon), end_lat = float(end_lat), end_lon = float(end_lon), start_node = NODE_COORDS[(float(start_lat), float(start_lon))], end_node = NODE_COORDS[(float(end_lat), float(end_lon))]))
            PASSENGERS.append(classes.Passenger(id = id, timestamp = time, start_lat = float(start_lat), start_lon = float(start_lon), end_lat = float(end_lat), end_lon = float(end_lon)))
            id += 1

def main():

    initialize()

    passenger_wait_times, driver_idle_times = [], [] # Metrics

    driver_queue = [] # Priority queue for driver by available time
    for driver in DRIVERS:
        heapq.heappush(driver_queue, (driver, driver.time))
    passenger_queue = deque(PASSENGERS) # Priority queue for passenger by ride request time (already sorted and no pushes so we use deque)


    while passenger_queue:

        # Match passenger and driver
        passenger = passenger_queue.popleft()

        try:
            driver, t = heapq.heappop(driver_queue)
        except:
            print(f'No more drivers available. Remaining passengers: {len(passenger_queue)}')
            print(f'Average Passenger Wait Time: {sum(passenger_wait_times) / len(passenger_wait_times)}')
            print(f'Average Driver Idle Time: {sum(driver_idle_times) / len(driver_idle_times)}')
            return

        # Check wait times (in minutes)
        passenger_wait_time = 0
        driver_idle_time = 0
        if driver.time < passenger.time: # Driver ready before passenger
            wait = passenger.time - driver.time
            driver_idle_time += wait.total_seconds() / 60
        elif driver.time > passenger.time: # Passenger ready before driver
            wait = driver.time - passenger.time
            passenger_wait_time += wait.total_seconds() / 60
        passenger_wait_times.append(passenger_wait_time)
        driver_idle_times.append(driver_idle_time)

        p = random.randint(1, 15)
        if p > 1: # Geometric random variable, expect every driver to do 10 rides per night
            driver.time += dt.timedelta(minutes = 10)
            heapq.heappush(driver_queue, (driver, driver.time))
    
    print(f'Average Passenger Wait Time: {sum(passenger_wait_times) / len(passenger_wait_times)}')
    print(f'Average Driver Idle Time: {sum(driver_idle_times) / len(driver_idle_times)}')

if __name__ == '__main__':
    main()