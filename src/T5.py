
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

import datastructures
reload(datastructures)
from datastructures import Grid
from datastructures import KDTree


### Data Objects
NODES = {} # <node_id: Node_Object>
NODE_COORDS = {} # <(lat, lon): Node_Object>
DRIVERS = []
PASSENGERS = []

### Preprocessed information about network
AVG_MPH = 0
NUM_ROADS = 0

### Based on sampling two points in NYC and calculating lat/lon mile distance
LON2MI = 45.5
LAT2MI = 60.0


KDTREE = None
PARTITION = None


def initialize():

    rootpath = os.path.dirname(os.getcwd())
    rootpath = os.path.join(rootpath, 'NotUber')
    
    global PARTITION
    PARTITION = Grid()
    
    ### Initialize nodes
    with open(rootpath + '/data/node_data.json', 'r') as v:
        n_reader = json.load(v)

    # Generate Node objects
    for node_id in n_reader:
        node = classes.Node(id = int(node_id), lat = n_reader[node_id]['lat'], lon = n_reader[node_id]['lon'])
        NODES[int(node_id)] = node
        NODE_COORDS[(n_reader[node_id]['lat'], n_reader[node_id]['lon'])] = node
        PARTITION.add_node(node)
    
    global KDTREE
    KDTREE = KDTree(NODES.values(), 0, 100)

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
        
            PARTITION.add_edge(neighbor)

    ### Initialize drivers
    with open(rootpath + '/data/drivers.csv', 'r') as d:
        _ = d.readline()
        d_reader = csv.reader(d)
        
        # Generate Driver objects
        id = 1 # IDs because the data doesn't come with them
        for d in d_reader:
            time, lat, lon = d
            driver = classes.Driver(id = id, timestamp = time, lat = float(lat), lon = float(lon))
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
            PASSENGERS.append(passenger)
            id += 1
            
    
    PARTITION.calc_avg_speeds()
    
    ### Average MPH on network
    AVG_MPH /= NUM_ROADS
    print(f'Average MPH: {AVG_MPH}')



def main():
    
    # Metrics
    passenger_wait_times, driver_idle_times = [], []
    total_ride_profit = 0
    
    driver_queue = deque(DRIVERS)
    passenger_queue = deque(PASSENGERS) # Priority queue for passenger by ride request time (already sorted and no pushes so we use deque)

    print('Running simulation...')
    i = 0
    start_time = time.time()
    while passenger_queue:
        if i >= 100:
            print(f'Time for {i} passengers: {time.time() - start_time} seconds')
            i = 0
            start_time = time.time()
        i+= 1

        # Match passenger and driver
        passenger = passenger_queue.popleft()
        
        # add all drivers that became available between now and when passenger arrived
        while len(driver_queue) > 0 and driver_queue[0].time < passenger.time:
            PARTITION.add_driver(driver_queue.popleft())
            
        # check if there are drivers currently on grid
        # if no drivers, add next few drivers to grid
        if PARTITION.driver_count == 0:
            print('No drivers available, looking into future drivers...')
            print('No drivers at time', passenger.time)
            print('Top driver at ', driver_queue[0].time)
            for i in range(10): # arbitrarily choose amount, we can tune for different results
                # Higher number means more likely we notice if a driver will appear close to passenger
                # But too high means we may need to do a lot more processing for future rides
                if len(driver_queue) <= 0: break
                PARTITION.add_driver(driver_queue.popleft())
        
        # if there are no drivers left and no drivers to add, we quit
        if PARTITION.driver_count == 0:
            print(f'No more drivers available. Remaining passengers: {len(passenger_queue)} minutes')
            print(f'Average Passenger Wait Time: {sum(passenger_wait_times) / len(passenger_wait_times)} minutes')
            print(f'Average Driver Idle Time: {sum(driver_idle_times) / len(driver_idle_times)} minutes')
            print(f'Average Driver Profit: {total_ride_profit / len(DRIVERS)} minutes')
            return

        # match passenger with driver
        eta, driver = PARTITION.get_closest_driver(passenger.coords, passenger.time)
        if driver == None:
            print('Error, found no drivers.')
            print(f'Available drivers: {PARTITION.driver_count}')
            print(f'Querying {passenger.coords}')
        
        # check if driver and passenger have assigned nodes
        if driver.node == None:
            dist, node = KDTREE.get_kNN(1, driver.coords)[0]
            driver.node = node
        if passenger.node == None:
            dist, node = KDTREE.get_kNN(1, passenger.coords)[0]
            passenger.node = node
        if passenger.end_node == None:
            dist, node = KDTREE.get_kNN(1, passenger.end_coords)[0]
            passenger.end_node = node
        
        # calculate actual time to reach passenger and to arrive at destination
        

        time_to_available = max(0, (passenger.time - driver.time).total_seconds() / 60)
        time_to_passenger = driver.node.shortest_path_a_star(passenger.node, passenger.time, AVG_MPH)
        time_to_destination = passenger.node.shortest_path_a_star(passenger.end_node, passenger.time + dt.timedelta(minutes=time_to_passenger), AVG_MPH)

        #print(f'Time to do graph search: {end_time - start_time} seconds')
        
        
        passenger_wait_time = time_to_available + time_to_passenger + time_to_destination
        total_ride_profit += time_to_destination - time_to_passenger
        
        passenger_wait_times.append(passenger_wait_time)
        
        

        p = random.randint(1, 15)
        if p > 1: # Geometric random variable, expect every driver to do 10 rides per night            
            # Update driver data
            PARTITION.move_driver_to(driver, passenger.end_node.coords)
            
            driver.node = passenger.end_node
            driver.time = passenger.time + dt.timedelta(minutes=passenger_wait_time)
        else:
            PARTITION.remove_driver(driver)
            
        
    
    print(f'Average Passenger Wait Time: {sum(passenger_wait_times) / len(passenger_wait_times)} minutes')
    #print(f'Average Driver Idle Time: {sum(driver_idle_times) / len(driver_idle_times)} minutes')
    print(f'Total Driver Profit: {total_ride_profit} minutes')
    print(f'Average Driver Profit: {total_ride_profit / len(DRIVERS)} minutes')



if __name__ == '__main__':
    START = time.time()
    print('Initializing...')
    initialize()
    print(f'Finished initializing in {time.time() - START} seconds.')
    
    print('Simulating rides')
    START = time.time() # Timing simulation
    main()
    END = time.time() # Timing simulation
    print(f'Simulation Runtime: {END - START} seconds')