The edges.csv file contains one row for every road segment. There is a header row naming the columns. The edges are symmetric in the sense that if there is a row for A --> B then there should be a row for B --> A, but the average speeds may differ depending on the direction.

For each row / road segment:
    - Column 0: "start_id" contains the node id of the source
    - Column 1: "end_id" contains the node id of the destination
    - Column 2: "length" contains the distance along the segment in miles
    - Columns 3 - 26: "weekday_0" ... "weekday_23" contain the average speed along the road segment in miles per hour on weekdays at different hours. 0 refers to midnight to 1 am...23 refers to the hour before midnight.
    - Columns 27 - 50: "weekend_0" ... "weekend_23" contain the average speed along the road segment in miles per hour on weekends at different hours. 0 refers to midnight to 1 am...23 refers to the hour before midnight.