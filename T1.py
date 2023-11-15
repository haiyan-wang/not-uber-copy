from importlib import reload
import classes
reload(classes)

import json
import csv
from collections import deque
import heapq

def initialize():
    
    ### Initialize nodes

    global NODES
    NODES = {} # <node_id: Node_Object>
    
    with open('node_data.json', 'r') as v:
        n_reader = json.load(v)
    
    for node_id in n_reader:
        NODES[int(node_id)] = classes.Node(id = node_id, lat = n_reader[node_id]['lat'], lon = n_reader[node_id]['lon'])

    ### Initialize edges

    with open('edges.csv', 'r') as e:
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

    ### Initializing drivers

    global DRIVERS
    DRIVERS = []

    with open('drivers.csv', 'r') as d:
        _ = d.readline()
        d_reader = csv.reader(d)

        for d in d_reader:
            DRIVERS.append(classes.Driver(*d))

    ### Initializing passengers
    
    global PASSENGERS
    PASSENGERS = []

    with open('passengers.csv', 'r') as p:
        _ = p.readline()
        p_reader = csv.reader(p)

        for p in p_reader:
            PASSENGERS.append(classes.Passenger(*p))

if __name__ == '__main__':
    initialize()

    i, j = 0, 0 # i is index for passengers, j is index for drivers
    time = 0
    q = deque() # queue of drivers
    ongoing_rides = [] # heap for ongoing rides
    passenger_q = deque() # queue of passengers

    time_before_assign, time_to_passenger, driver_idle_time = 0, 0, 0

    while i < len(PASSENGERS):
        passenger_q.append((PASSENGERS[i], PASSENGERS[i].time))
        time = passenger_q[-1][1] # update time

        # adds new drivers and completed rides back into queue in order by time
        while (j < len(DRIVERS) and DRIVERS[j].time < time) or (ongoing_rides and ongoing_rides[0][1] < time):
            if DRIVERS and (not ongoing_rides or DRIVERS[j] < ongoing_rides[0][1]):
                q.append((DRIVERS[j], DRIVERS[j].time))
                j += 1
            else:
                t, driver = heapq.heappop(ongoing_rides)
                q.append((driver, t))

        if not q:
            i += 1
            continue

        while passenger_q and q:
            new_passenger, passenger_time = passenger_q.popleft()
            paired_driver, driver_time = q.popleft()

            time_before_assign += max(driver_time, passenger_time) - passenger_time
            driver_idle_time += max(driver_time, passenger_time) - driver_time
        
            # how long ride takes
            dt = paired_driver.node.shortest_path(new_passenger.start_node) * 3600

            time_to_passenger = dt

            dt += new_passenger.start_node.shortest_path(new_passenger.end_node) * 3600

            # push ride to heap, update location of driver
            heapq.heappush(ongoing_rides, (max(passenger_time, driver_time) + dt, paired_driver))
            paired_driver.node = new_passenger.end_node

        i += 1 

    print(f'Average time before ride is assigned: {time_before_assign/len(PASSENGERS)}')
    print(f'Average time for driver to reach passenger: {time_to_passenger/len(PASSENGERS)}')
    print(f'Average time driver is idle: {time_before_assign/len(DRIVERS)}')

