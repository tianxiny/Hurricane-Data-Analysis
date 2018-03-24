
from pygeodesy import ellipsoidalVincenty as ev
import datetime as dt

def flip_direction(direction: str) -> str:
    # Adapted from IS590PR Examples, by J. Weible
    """Given a compass direction 'E', 'W', 'N', or 'S', return the opposite.
    Raises exception with none of those.
    :param direction: a string containing 'E', 'W', 'N', or 'S'
    :return: a string containing 'E', 'W', 'N', or 'S'
    >>> flip_direction('E')
    'W'
    >>> flip_direction('S')
    'N'
    >>> flip_direction('SE')  # test an unsupported value
    Traceback (most recent call last):
    ...
    ValueError: Invalid or unsupported direction SE given.
    """
    if direction == 'E':
        return 'W'
    elif direction == 'W':
        return 'E'
    elif direction == 'N':
        return 'S'
    elif direction == 'S':
        return 'N'
    else:
        raise ValueError('Invalid or unsupported direction {} given.'.format(direction))

def myLatLon(lat: str, lon: str) -> ev.LatLon:
    # Adapted from IS590PR Examples, by J. Weible
    """Given a latitude and longitude, normalize the longitude if necessary,
    to return a valid ellipsoidalVincenty.LatLon object.
    :param lat: the latitude as a string
    :param lon: the longitude as a string
    >>> a = ev.LatLon('45.1N', '2.0E')
    >>> my_a = myLatLon('45.1N', '2.0E')
    >>> a == my_a
    True
    >>> my_b = myLatLon('45.1N', '358.0W')
    >>> a == my_b  # make sure it normalizes properly
    True
    >>> myLatLon('15.1', '68.0')
    LatLon(15°06′00.0″N, 068°00′00.0″E)
    """
    lon_dir = ''
    if lon[-1] in ['E', 'W']:
        # parse string to separate direction from number portion:
        lon_num = float(lon[:-1])
        lon_dir = lon[-1]
    else:
        lon_num = float(lon)
    if lon_num > 180.0:  # Does longitude exceed range?
        lon_num = 360.0 - lon_num
        lon_dir = flip_direction(lon_dir)
        lon = str(lon_num) + lon_dir
    return ev.LatLon(lat, lon)

def hours_elapsed(t1: dt.datetime, t2: dt.datetime) -> float:
    # Adapted from IS590PR Examples, by J. Weible
    """Given 2 datetime objects, return the number of elapsed hours between them (as a float).
    :param t1: a datetime object
    :param t2: a datetime object
    :return: elapsed hours between t1 & t2, as a float
    >>> hours_elapsed(dt.datetime(1864, 8, 26, 0, 0), dt.datetime(1864, 9, 1, 6, 0))
    150.0
    """
    diff = abs(t2 - t1)  # get the difference of time between
    return diff.total_seconds() / 3600.0  # convert result into hours as a float:

def get_max_wind_and_datetime(storm: list) -> dict:
    # Adapted from IS590PR Examples, by J. Weible
    """Given the detailed records about a specific storm, as a list,
    return a dictionary containing the highest maximum sustained wind (in knots),
    and when it first occurred (datetime).
    :param storm: storm details extracted from a hurdat file, as a list, which is a result of read_n_parse_a_storm()
    :return: a dictionary with 2 keys: the highest maximum wind and the time of occurrence
    """
    highest = 0  # start at zero
    datetime = dt.datetime # declare the 'datetime' type
    for row in storm: # loop through the rows
        if row[6] > highest:
            highest = row[6]
            datetime = row[2]
    if highest == 0: # the max wind doesn't exist
        datetime = 'NA'
    return {'maxwind': highest, 'datetime': datetime}

def get_count_landfall(storm: list) -> int:
    """Given the detailed records about a specific storm, as a list,
    return the number of landfalls occurred.
    :param storm: storm details extracted from a hurdat file, as a list, which is a result of read_n_parse_a_storm()
    :return: the number of landfalls recorded, as an integer
    """
    count = 0
    for row in storm:  # loop through the rows
        if row[3] == 'L':
            count += 1
    return count

def degree_normalized(degree: int) -> int:
    """Given any degree, return a degree ranging from 0 (inclusive) to 360 (exclusive).
    :param degree: a degree in any range, as an integer
    :return: a degree in [0, 360), as an integer
    >>> degree_normalized(420)
    60
    """
    if degree < 0:
        n_degree = degree + 360 * (abs(degree) // 360) # make sure the result is in [0, 360)
    elif degree < 360:
        n_degree = degree
    else:
        n_degree = degree - 360 * (abs(degree) // 360)
    return n_degree

def degree_2_quadrant(degree) -> str:
    """Given a normalized degree, return the corresponding quadrant.
    :param d: a normalized degree, as an integer
    :return: the quadrant, as a string, 'NE', 'SE', 'SW', 'NW', return 'NA' if out of range
    >>> degree_2_quadrant(45)
    'NE'
    >>> degree_2_quadrant(300)
    'NW'
    >>> degree_2_quadrant(365)
    'NA'
    """
    if degree < 0:
        quadrant = 'NA'
    elif degree < 90:
        quadrant = 'NE'
    elif degree < 180:
        quadrant = 'SE'
    elif degree < 270:
        quadrant = 'SW'
    elif degree < 360:
        quadrant = 'NW'
    else:
        quadrant = 'NA'
    return quadrant

def read_n_parse_a_storm(fin, storm_ID: str = None):
    ''' Given a specific dataset and a storm ID, (CASE I) find the storm,
    parse the detailed data and return a storm record as a list.
    The date, time, latitude, longitude will be converted to datetime and LatLon by using datetime and pygeodesy respectively.
    The function will return None if the storm is not found and alert the user to check the storm ID.
    For example,
    [['AL021851', 'UNNAMED', datetime.datetime(1851, 7, 5, 12, 0), '', 'HU', LatLon(22°12′00.0″N, 097°36′00.0″W), 80, -999, -999, -999, -999, -999, -999, -999, -999, -999, -999, -999, -999, -999]]
    **(CASE II) Alternatively, the user can skip inputting the storm_ID where the storm_ID is set as None as the default.
    It is designed to go through the whole dataset, working in a while loop.
    As it hits the end of file, it returns None.
    :param dataset_raw: the file object, already opened
    :param storm_ID: the ID of a specific storm, as a string, like 'AL012015', or input None to iterate
    :return: a list of lists containing all the records of a specific storm, or None
    '''
    storm = []
    if storm_ID == None: # used to go through the whole dataset (CASE I)
        line = fin.readline()
        if line != '': # the normal lines
            header = line # the pointer moves automatically
            header_split = [instance.strip() for instance in header.split(',')]
            storm_ID = header_split[0]
            storm_name = header_split[1]
            nr_data_lines_to_read = int(header_split[2]) # make sure all the data lines are extracted
        else: # the end of file
            return None
    else: # used to locate a specific storm (CASE II)
        while True:
            line = fin.readline()
            if storm_ID in line: # go over the file and find the line where the storm ID is located
                header = line
                header_split = [instance.strip() for instance in header.split(',')]
                storm_name = header_split[1]
                nr_data_lines_to_read = int(header_split[2])
                break
            elif line == '': # reach the end of file and fail to find a storm with the ID input
                print('Cannot find a storm with ID ' + str(storm_ID) + '. Please check if the storm ID is correct.')
                return None
            else:
                continue
    for nr_lines in range(nr_data_lines_to_read):
        line = fin.readline() # read the data lines of a specific storm into a list
        line_split = [instance.strip() for instance in line.split(',')] # split into list of strings at commas
        line_ready = line_split[:-1] # throw away the last value which is a newline
        line_ready[0] = dt.datetime.strptime(''.join(line_ready[0:2]), '%Y%m%d%H%M') # convert the date and time into datetime
        del line_ready[1] # merge the two columns
        line_ready[3] = myLatLon(line_ready[3],line_ready[4]) # convert the latitude and longitude
        del line_ready[4] # merge the two columns
        for i in range(0, len(line_ready[4:])):
            line_ready[4+i]= int(line_ready[4+i]) # force the numerical columns into integers
        storm.append([storm_ID, storm_name] + line_ready) # add the storm ID and strom name as the leading two columns
    return storm

def get_positions(storm: list) -> list:
    """Given a storm, extract the positions from it.
    :param storm: storm details extracted from a hurdat file, as a list, which is a result of read_n_parse_a_storm()
    :return: positions in all records, as a list
    """
    positions = []
    for item in storm:
        positions.append(item[5])
    return positions

def path_distance(storm: list) -> list:
    """Given a storm, compute the distance between each two points.
    Raises exception when there is only one record.
    :param storm: storm details extracted from a hurdat file, as a list, which is a result of read_n_parse_a_storm()
    :return: distances between each two points, as a list
    """
    distances = []
    positions = get_positions(storm)
    for i in range(len(positions) - 1):
        try:
            distance = positions[i].distanceTo(positions[i + 1]) / 1852.0 # 1 Nautical Mile = 1852 Meters
        except ValueError: # in case there is only 1 record
            distance = 0
        distances.append(distance)
    return distances

def path_propagation_speed(storm: list) -> list:
    """Given a storm, compute the propagation speed between each two points.
    Raises exception when there is only one record.
    :param storm: storm details extracted from a hurdat file, as a list, which is a result of read_n_parse_a_storm()
    :return: a list of propagation speeds
    """
    timepoints = []
    propagation_speeds = []
    for row in storm:
        timepoints.append(row[2])
    for i in range(len(timepoints) - 1):
        try: # compute the storm center moved divided by the corresponding time span
            time_span = hours_elapsed(timepoints[i], timepoints[i + 1])
            propagation_speed = path_distance(storm)[i] / time_span
        except ZeroDivisionError: # in case there is only 1 record
            propagation_speed = 0
        propagation_speeds.append(propagation_speed)
    return(propagation_speeds)

def storm_report(storm) -> dict:
    """Given a specific storm, report the ID, name, date range,
    highest Maximum sustained wind (in knots) with time of occurrence, number of landfalls,
    [As required in Phase A.1]
    total distance a storm center moves, and
    [As required in Phase B.1]
    maximum propagation speed and mean propagation speed.
    [As required in Phase B.2]
    For example:
    {'ID': 'AL051852', 'Name': 'UNNAMED', 'Start Date': '1852-10-06', 'End Date': '1852-10-11',
    'Max Wind (in knots)': 90, 'When': '1852-10-06 00:00', 'Number of Landfalls': 1,
    'Total Distance (in NM)': 2434.8878250299113,
    'Max Speed': 37.75194505360013, 'Mean Speed': 17.559855234087742}
    Raises exception if the max wind doesn't exist, or if there is only one record.
    :param storm: storm details extracted from a hurdat file, as a list, which is a result of read_n_parse_a_storm()
    :return: a dictionary containing all the fields desired
    """
    each_storm_summary = {}
    storm_ID = storm[0][0]
    storm_name = storm[0][1]
    start_date = storm[0][2] # first row
    end_date = storm[-1][2] # last row
    max_wind = get_max_wind_and_datetime(storm)['maxwind']
    try:
        max_wind_date_time = get_max_wind_and_datetime(storm)['datetime'].strftime("%Y-%m-%d %H:%M")
    except AttributeError: # in rare cases, the sustained wind keeps -99, see 'AL011967'
        max_wind_date_time = 'NA'
    landfall_count = get_count_landfall(storm)
    total_distance = 0 # start from 0, an accumulator
    distances = path_distance(storm)
    for distance in distances:
        total_distance += distance
    try:
        max_speed = max(path_propagation_speed(storm))
    except ValueError: # in case there is only 1 record
        max_speed = 'NA'
    try:
        mean_speed = sum(path_propagation_speed(storm)) / len(path_propagation_speed(storm))
    except ZeroDivisionError: # in case there is only 1 record
        mean_speed = 'NA'
    each_storm_summary = {'ID': storm_ID, 'Name': storm_name, 'Start Date': start_date.strftime("%Y-%m-%d"),
                          'End Date': end_date.strftime("%Y-%m-%d"), 'Max Wind (kn)': max_wind,
                          'When': max_wind_date_time, 'Number of Landfalls': landfall_count,
                          'Total Distance (NM)': total_distance,
                          'Max Speed (NM/h)': max_speed,
                          'Mean Speed (NM/h)': mean_speed}
    return each_storm_summary

def hypothetical_quadrant(storm) -> list:
    """Given a storm, compute the hypothetical quadrants the highest winds (and therefore longest radius of high wind)
    should typically be in. The lower bound is set as bearing + 45 whereas the upper bound is set as bearing + 90.
    Raises exception when there is only one record.
    :param storm: storm details extracted from a hurdat file, as a list, which is a result of read_n_parse_a_storm()
    :return: the hypothetical quadrants lower bounds and upper bounds for each record, as a list
    """
    positions = get_positions(storm)
    hypo_quadrants_lower = []
    hypo_quadrants_upper = []
    for i in range(len(positions) - 1):
        try: # compute the initial compass bearing (in degrees)
            degree = positions[i].bearingTo(positions[i + 1])
        except ValueError: # in case there is only 1 record or the two positions are identical
            degree = 0
        hypo_degree_lower = degree_normalized(degree + 45) # handle the cases where the sum exceeds 360
        hypo_degree_upper = degree_normalized(degree + 90)
        hypo_quadrant_lower = degree_2_quadrant(hypo_degree_lower)
        hypo_quadrant_upper = degree_2_quadrant(hypo_degree_upper)
        hypo_quadrants_lower.append(hypo_quadrant_lower)
        hypo_quadrants_upper.append(hypo_quadrant_upper)
    return [hypo_quadrants_lower, hypo_quadrants_upper]

def actual_quadrant(storm) -> list:
    """Given a storm, compute the actual quadrants the highest winds (and therefore longest radius of high wind)
    are in, based on the highest level of non-zero radii (64-kt, 50-kt, or 34-kt) at that time.
    Raises exception when there is only one record and/or no available record can be used to determine the actual quadrant.
    :param storm: storm details extracted from a hurdat file, as a list, which is a result of read_n_parse_a_storm()
    :return: the actual quadrants for each record, as a list
    """
    real_quadrants = []
    for row in storm[1:]: # the first row is always the start point
        real_quadrant = 'NA'
        if len(storm) == 1:
            continue
        else:
            index = 0 # used to store the column number, working REVERSELY, check 64-kt, then 50-kt, and then 34-kt
            while row[index - 1] + row[index - 2] + row[index - 3] + row[index - 4] <= 0 and index > -7:
                # exclude the situation where the four numbers all equal to zero or -999, and stops when the twelve numbers are all iterated
                index -= 4 # move two the next four column at left for each step
                max_val = max(row[index - 1], row[index - 2], row[index - 3], row[index - 4])
                if row[index - 1] == row[index - 2] == row[index - 3] == row[index - 4]: # make no sense
                    continue
                else:
                    if max_val == row[index - 4]: # highest maximum extent in northeastern quadrant
                        real_quadrant = 'NE'
                        break
                    elif max_val == row[index - 3]: # highest maximum extent in southeastern quadrant
                        real_quadrant = 'SE'
                        break
                    elif max_val == row[index - 2]: # highest maximum extent in southwestern quadrant
                        real_quadrant = 'SW'
                        break
                    elif max_val == row[index - 1]: # highest maximum extent in northwestern quadrant
                        real_quadrant = 'NW'
                        break
                    else:
                        continue
            real_quadrants.append(real_quadrant)
    return real_quadrants

def accuracy_rate(actual, hypo_lower, hypo_upper):
    """Given the actual quadrant list and two hypothetical quadrant lists, calculate the total events and sucess events of a storm.
    The actual one meets either the lower bound or the upper bound is considered a success.
    The function returns a tuple (number of successful events, number of total events).
    :param actual: the actual quadrants for a storm, a list, which is the result of actual_quadrant()
    :param hypo_lower: the lower bound of hypothetical quadrants for a storm, a list, which is the result of actual_quadrant()
    :param hypo_upper: the upper bound of hypothetical quadrants for a storm, a list, which is the result of actual_quadrant()
    :return: a tuple (Correct, Total)
    """
    Correct = 0 # start from 0
    Total = 0
    for i in range(len(actual)):
        if actual[i] != 'NA': # exclude the situations that the actual quadrant cannot be determined
            if actual[i] == hypo_lower[i] or actual[i] == hypo_upper[i]: # in either quadrant
                Correct += 1
                Total += 1
            else:
                Total += 1
    return (Correct, Total)

if __name__ == '__main__':
    while True:
        input_keyword = input("Would you like to review the details of every storms (Y=Yes, N=No)? ")
        if input_keyword[0] in ["Y", "y", "T", "t"]:
            storm_details_flag = True
            break
        elif input_keyword[0] in ["N", "n", "F", "f"]:
            storm_details_flag = False
            break
        else:
            print("Please check the input.")
    while True:
        input_keyword = input("Would you like to review the summary by year (Y=Yes, N=No)? ")
        if input_keyword[0] in ["Y", "y", "T", "t"]:
            summary_by_year_flag = True
            break
        elif input_keyword[0] in ["N", "n", "F", "f"]:
            summary_by_year_flag = False
            break
        else:
            print("Please check the input.")
    try:
        dataset = input("Please input the filename of a hurdat dataset (e.g. hurdat2-1851-2016-041117.txt): ")
        storm_correct = storm_total = 0
        with open(dataset, 'r', encoding='utf8') as fin:
            print("Loading... Please wait...")
            if storm_details_flag == True:
                print("Each Storm:")
            all_storm = [] # to read all storm in, one for each step
            while True:
                storm = read_n_parse_a_storm(fin, )
                if storm == None:
                    break
                if storm_details_flag == True:
                    print(storm_report(storm))
                all_storm += storm
                hypo_lower = hypothetical_quadrant(storm)[0]
                hypo_upper = hypothetical_quadrant(storm)[1]
                actual = actual_quadrant(storm)
                (correct, total) = accuracy_rate(actual, hypo_lower, hypo_upper)
                storm_correct += correct
                storm_total += total
            storm_accuracy_rate = storm_correct / storm_total
            print(str(storm_accuracy_rate * 100) +"% cases support the hypothesis.")
    except FileNotFoundError:
        print("Cannot find the file requested. Please check the filename.")
    while True:
        input_keyword = input("Would you like to check a specific storm (Y=Yes, N=No)? ")
        if input_keyword[0] in ["Y", "y", "T", "t"]:
            single_storm_flag = True
            break
        elif input_keyword[0] in ["N", "n", "F", "f"]:
            single_storm_flag = False
            break
        else:
            print("Please check the input.")
    if single_storm_flag == True:
        dataset = input("Please input the filename of a hurdat dataset (e.g. hurdat2-1851-2016-041117.txt): ")
        storm_ID = input("Please input a valid storm ID (e.g. AL012015): ")
        try:
            with open(dataset, 'r', encoding='utf8') as fin:
                storm = read_n_parse_a_storm(fin, storm_ID)
                print(storm_report(storm))
        except FileNotFoundError:
            print("Cannot find the file requested. Please check the filename.")
        except ValueError:
            print("The storm ID is not valid.")
