import datetime as dt
import math
import heapq

import classes

# Pre-computed values from prior pre-processing
MIN_LAT, MIN_LON, MAX_LAT, MAX_LON = 40.49, -74.26, 40.92, -73.69
LAT_RANGE = MAX_LAT - MIN_LAT
LON_RANGE = MAX_LON - MIN_LON
GRID_WIDTH, GRID_HEIGHT = 20, 30

class GridSpace:
    def __init__(self, lat_idx, lon_idx) -> None:
        self.nodes = set() # nodes within grid space
        self.edges = []
        self.edge_length = []
        self.total_length = 0
        
        self.drivers = set() # drivers within grid space
        min_coords = Grid.idx2min_coords((lat_idx, lon_idx))
        max_coords = Grid.idx2min_coords((lat_idx+1, lon_idx+1))
        self.lat_bounds = (min_coords[0], max_coords[0])
        self.lon_bounds = (min_coords[1], max_coords[1])
        self.weekday_avg_mph = []
        self.weekend_avg_mph = []
        
        
    def add_node(self, node:classes.Node):
        self.nodes.add(node)
        
    def add_edge(self, edge:classes.Edge, length=None):
        self.edges.append(edge)
        
        if length is not None:
            self.edge_length.append(length)
            self.total_length += length
            return
        
        self.edge_length.append(self.get_edge_intersecting_length(edge))
        self.total_length += self.edge_length[-1]
    
    @staticmethod
    def get_segments_intersection(x1, y1, x2, y2, x3, y3, x4, y4):
        # via wikipedia
        x1_x2 = x1 - x2
        x1_x3 = x1 - x3
        x3_x4 = x3 - x4
        y1_y2 = y1 - y2
        y1_y3 = y1 - y3
        y3_y4 = y3 - y4
        
        d = (x1_x2)*(y3_y4) - (y1_y2)*(x3_x4)
        if d == 0: return None
        
        t = ((x1_x3)*(y3_y4) - (y1_y3)*(x3_x4)) / d
        u = ((x1_x3)*(y1_y2) - (y1_y3)*(x1_x2)) / d
        
        if t < 0 or t > 1 or u < 0 or u > 1: return None
        
        p_x = x1 - t*x1_x2
        p_y = y1 - t*y1_y2
        
        return (p_x, p_y)
    
    def get_edge_intersecting_length(self, edge:classes.Edge):
        if edge.start_node in self.nodes and edge.end_node in self.nodes: return edge.length
        
        int_node = edge.start_node
        ext_node = edge.end_node
        
        if ext_node in self.nodes:
            int_node = edge.end_node
            ext_node = edge.start_node
        
        vert_above = ext_node.coords[1] > int_node.coords[1]
        
        top_left = (self.lat_bounds[0], self.lon_bounds[1])
        top_right = (self.lat_bounds[1], self.lon_bounds[1])
        bot_left = (self.lat_bounds[0], self.lon_bounds[0])
        bot_right = (self.lat_bounds[1], self.lon_bounds[0])
        
        if ext_node.coords[0] > self.lat_bounds[0] and ext_node.coords[0] < self.lat_bounds[1]:
            # horizontally within region, either directly above or below
            if vert_above:
                # directly above
                intersection = GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                   *top_left, *top_right)
            else:
                # directly below
                intersection = GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                   *bot_left, *bot_right)
        
        else: # on either end horizontally
            horiz_right = ext_node.coords[0] > int_node.coords[0]
            if ext_node.coords[1] > self.lon_bounds[0] and ext_node.coords[1] < self.lon_bounds[1]:
                # vertically center
                if horiz_right: # right side
                    intersection = GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                       *top_right, *bot_right)
                else: # left side
                    intersection = GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                       *top_left, *bot_left)
                
            else: # in corners, requiring 2 segment checks
                if vert_above:
                    # check if intersect with top
                    intersection = GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                       *top_left, *top_right)
                    # otherwise, check either side
                    if intersection is None:
                        intersection = (GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                               *top_right, *bot_right)
                                        if horiz_right else
                                        GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                               *top_left, *bot_left))
                else:
                    # check if intersect with bot
                    intersection = GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                       *bot_left, *bot_right)
                    # otherwise, check either side
                    if intersection is None:
                        intersection = (GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                               *top_right, *bot_right)
                                        if horiz_right else
                                        GridSpace.get_segments_intersection(*int_node.coords, *ext_node.coords,
                                                                               *top_left, *bot_left))
                        
        if intersection is None:
            print(f'Failed to find intersection between edge from {edge.start_node.coords} to {edge.end_node.coords} with region defined by lat bounds {self.lat_bounds} and lon bounds {self.lon_bounds}')
            return None
        # Calculate length of resulting segment
        dx = int_node.coords[0] - intersection[0]
        dy = int_node.coords[1] - intersection[1]
        return math.sqrt(dx*dx + dy*dy)
                
        
    def calc_avg_mph(self):
        if self.total_length == 0:
            # there are no edges in this region, so we say it takes infinite time
            self.weekday_avg_mph = [float('inf')] * 24
            self.weekend_avg_mph = [float('inf')] * 24
            return
        
        # for each edge at each time step, calculate weightings and store average mph at each hour
        
        self.weekday_avg_mph = [0] * 24
        self.weekend_avg_mph = [0] * 24
        
        # Each edge is weighted by the length it takes up in the gridspace
        for i, edge in enumerate(self.edges):
            for hour in range(24):
                self.weekday_avg_mph[hour] += self.edge_length[i] * float(edge.weekday_speeds[hour])
                self.weekend_avg_mph[hour] += self.edge_length[i] * float(edge.weekend_speeds[hour])
                
        for hour in range(24):
            self.weekday_avg_mph[hour] /= self.total_length
            self.weekend_avg_mph[hour] /= self.total_length
    
    def add_driver(self, driver):
        self.drivers.add(driver)
        
    def remove_driver(self, driver):
        self.drivers.remove(driver)
        
    def get_closest_driver(self, coords, time:dt.datetime):
        hour = time.hour
        weekday = time.isoweekday() < 6
        min_time = float('inf')
        best_driver = None
        for driver in self.drivers:
            # use manhattan distance and current time to estimate time to arrive
            eta = abs(driver.coords[0] - coords[0]) + abs(driver.coords[1] - coords[1])
            eta *= self.weekday_avg_mph[hour] if weekday else self.weekend_avg_mph[hour]
            eta *= 60 # convert to minutes
            
            # if driver hasn't arrived yet, add time till arrival
            if driver.time > time:
                eta += (driver.time - time).total_seconds() / 60
            
            if eta < min_time:
                min_time = eta
                best_driver = driver
        
        return (min_time, best_driver)
            
        
class Grid:
    @staticmethod
    def coord2idx(coords):
        lat_idx = math.floor((coords[0] - MIN_LAT) / LAT_RANGE * GRID_WIDTH)
        lon_idx = math.floor((coords[1] - MIN_LON) / LON_RANGE * GRID_HEIGHT)
        lat_idx = max(0, min(lat_idx, GRID_WIDTH-1))
        lon_idx = max(0, min(lon_idx, GRID_HEIGHT-1))
        return (lat_idx, lon_idx)
    @staticmethod
    def idx2min_coords(idx):
        lat = idx[0] / GRID_WIDTH * LAT_RANGE + MIN_LAT
        lon = idx[1] / GRID_HEIGHT * LON_RANGE + MIN_LON
        return (lat, lon)
    
    def __init__(self) -> None:
        self.grid = [[GridSpace(lat_idx, lon_idx) for lon_idx in range(0, GRID_HEIGHT)]
                        for lat_idx in range(0, GRID_WIDTH)]
        self.driver_count = 0
        
    def calc_avg_speeds(self):
        for lat_idx in range(GRID_WIDTH):
            for lon_idx in range(GRID_HEIGHT):
                self.grid[lat_idx][lon_idx].calc_avg_mph()
    
    def add_node(self, node) -> None:
        self.get_grid_space(node.coords).add_node(node)
        
    def add_edge(self, edge:classes.Edge):
        l = self.get_grid_space(edge.start_node.coords).get_edge_intersecting_length(edge)
        self.get_grid_space(edge.start_node.coords).add_edge(edge, l)
        self.get_grid_space(edge.end_node.coords).add_edge(edge, edge.length - l)
    
    def get_grid_space(self, coords) -> GridSpace:
        idx = Grid.coord2idx(coords)
        return self.grid[idx[0]][idx[1]]
    
    def add_driver(self, driver) -> None:
        self.driver_count += 1
        coords = driver.coords #if driver.node is None else driver.node.coords
        self.get_grid_space(coords).add_driver(driver)
    
    def remove_driver(self, driver):
        self.driver_count -= 1
        coords = driver.coords #if driver.node is None else driver.node.coords
        self.get_grid_space(coords).remove_driver(driver)
        
    def move_driver_to(self, driver:classes.Driver, coords):
        self.get_grid_space(driver.coords).remove_driver(driver)
        driver.coords = coords
        self.get_grid_space(coords).add_driver(driver)
    
        
    def get_closest_driver(self, coords, time) -> classes.Driver:
        # perform floodfill on grid searching for best driver
        idx_to_search = [Grid.coord2idx(coords)]
        visited = set()
        
        min_time = float('inf')
        best_driver = None
        
        while len(idx_to_search) > 0 and best_driver is None:
            next_to_search = []
            while len(idx_to_search) > 0:
                idx = idx_to_search.pop()
                if idx in visited: continue
                visited.add(idx)
                
                # search this gridspace for closest driver
                eta, driver = self.grid[idx[0]][idx[1]].get_closest_driver(coords, time)
                if eta < min_time:
                    min_time = eta
                    best_driver = driver
                
                if best_driver is None:
                    # floodfill to nearby indices
                    next_idx = (idx[0]+1,idx[1])
                    if next_idx not in visited and next_idx[0] < GRID_WIDTH: next_to_search.append(next_idx) 
                    next_idx = (idx[0]-1,idx[1])
                    if next_idx not in visited and next_idx[0] >= 0: next_to_search.append(next_idx)
                    next_idx = (idx[0],idx[1]+1)
                    if next_idx not in visited and next_idx[1] < GRID_HEIGHT: next_to_search.append(next_idx)
                    next_idx = (idx[0],idx[1]-1)
                    if next_idx not in visited and next_idx[1] >= 0: next_to_search.append(next_idx)
            
            idx_to_search = next_to_search
            
        return (min_time, best_driver)
        



class KDTree:
    left = None
    right = None
    nodes = None # if at leaf, this contains all nodes in this region
    depth = 0
    
    split_val = None
    x_bounds = None
    y_bounds = None
    
    @staticmethod
    def selector(depth:int): return int(depth % 2 != 0)
    @staticmethod
    def dist(coord1, coord2):
        # Euclidean distance
        d1 = coord2[0] - coord1[0]
        d2 = coord2[1] - coord1[1]
        return math.sqrt(d1*d1 + d2*d2)
    @staticmethod
    def dist_to_rect(point, rect_x_bounds, rect_y_bounds):
        dx = max(rect_x_bounds[0] - point[0], 0, point[0] - rect_x_bounds[1])
        dy = max(rect_y_bounds[0] - point[1], 0, point[1] - rect_y_bounds[1])
        return math.sqrt(dx*dx + dy*dy)
    
    # return the distance from the bounds of this region and a point
    def dist_to_point(self, point):
        return KDTree.dist_to_rect(point, self.x_bounds, self.y_bounds)
    
    def __init__(self, nodes, depth: int, max_depth: int,
                 minx=MIN_LAT, maxx=MAX_LAT, miny=MIN_LON, maxy=MAX_LON) -> None:
        self.depth = depth
        self.x_bounds = (minx, maxx)
        self.y_bounds = (miny, maxy)
        
        # If reached max split depth, make leaf
        if depth >= max_depth:
            self.nodes = nodes
            return
        
        # Select lat if even depth, lon if odd depth
        selector = KDTree.selector(depth)
        
        sorted_nodes = sorted(nodes, key=lambda x: x.coords[selector])
        
        median = int(len(sorted_nodes) / 2)
        self.split_val = sorted_nodes[median].coords[selector]
        #print(f'Split on {"lon" if selector else "lat"} at {self.split_val}')
        
        left_nodes = sorted_nodes[:median]
        right_nodes = sorted_nodes[median:]
        
        if selector == 0:
            if len(left_nodes) > 0:
                self.left = KDTree(left_nodes, depth+1, max_depth,
                                    minx, self.split_val, miny, maxy)
            if len(right_nodes) > 0:
                self.right = KDTree(right_nodes, depth+1, max_depth,
                                    self.split_val, maxx, miny, maxy)
        else:
            if len(left_nodes) > 0:
                self.left = KDTree(left_nodes, depth+1, max_depth,
                                    minx, maxx, miny, self.split_val)
            if len(right_nodes) > 0:
                self.right = KDTree(right_nodes, depth+1, max_depth,
                                    minx, maxx, self.split_val, maxy)
        
        if self.left == None and self.right == None:
            # Leaf node, assign single value to nodes
            self.nodes = nodes
    
    def kNN_helper(self, k, query_coords, k_closest_heap):#, search_list = None):
        #seen_nodes = []
        #if (search_list is not None and len(search_list) > 0): seen_nodes = search_list[-1][2].copy()
        
        # if at a leaf, check if any nodes are closer
        if self.nodes:
            for node in self.nodes:
                #seen_nodes.append(node)
                
                d = KDTree.dist(node.coords, query_coords)
                # If closer, or heap not filled, add new point
                if len(k_closest_heap) < k or d < -k_closest_heap[0][0]:
                    heapq.heappush(k_closest_heap, (-d, node))
                    # if more than k stored, pop worst
                    if len(k_closest_heap) > k: heapq.heappop(k_closest_heap)
            
            #if search_list is not None: search_list.append((self, k_closest_heap.copy(), seen_nodes, self.dist_to_point(query_coords)))
            return
        
        #if search_list is not None: search_list.append((self, k_closest_heap.copy(), seen_nodes, self.dist_to_point(query_coords)))
        
        # otherwise, traverse
        selector = KDTree.selector(self.depth)
        
        # check which side to prioritize
        search_side = self.left
        opp_side = self.right
        if query_coords[selector] > self.split_val:
            search_side = self.right
            opp_side = self.left
        
        # recurse
        if search_side is not None and (len(k_closest_heap) < k or
            search_side.dist_to_point(query_coords) < -k_closest_heap[0][0]):
            search_side.kNN_helper(k, query_coords, k_closest_heap)#, search_list)
            
        #if (search_list is not None and len(search_list) > 0): seen_nodes = search_list[-1][2].copy()
        #if search_list is not None: search_list.append((self, k_closest_heap.copy(), seen_nodes, self.dist_to_point(query_coords)))
        
        # check if other side should be searched
        if opp_side is not None and (len(k_closest_heap) < k or
            opp_side.dist_to_point(query_coords) < -k_closest_heap[0][0]):
            opp_side.kNN_helper(k, query_coords, k_closest_heap)#, search_list)
            
        #if (search_list is not None and len(search_list) > 0): seen_nodes = search_list[-1][2].copy()
        #if search_list is not None: search_list.append((self, k_closest_heap.copy(), seen_nodes, self.dist_to_point(query_coords)))
        
        
    def get_kNN(self, k, query_coords):
        #search_list = []
        knn_list = []
        self.kNN_helper(k, query_coords, knn_list)#, search_list)
        return knn_list#, search_list
    