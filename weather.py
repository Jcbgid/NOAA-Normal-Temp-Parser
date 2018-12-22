import requests
import datetime
from prettytable import PrettyTable
import argparse

used_real_nZip = None
used_real_fZip = None
used_real_day = None
used_real_month = None

WUNDERGROUND_KEY = None


def clean_temps(in_data):
    data_start = 2
    invalid_chars = "CSRPQ"
    for point in range(len(in_data)):
        for temp_index in range(data_start, len(in_data[point])):

            # Remove data info designators and converts data to proper scale
            in_data[point][temp_index] = in_data[point][temp_index].rstrip(invalid_chars)
            in_data[point][temp_index] = float(in_data[point][temp_index]) / 10

        # Remove invalid month terminators from data set
        in_data[point] = [x for x in in_data[point] if x != -888.8]


def clean_dates(in_data):
    data_location = 1
    for point in in_data:
        point[data_location] = point[data_location].lstrip("0")
        point[data_location] = int(point[data_location])
    return in_data


def read_data_lines(in_file, station_id):
    inline = []
    for line in in_file:
        if line.split()[0] == station_id:
            inline.append(line.split())
    clean_temps(inline)
    clean_dates(inline)
    return inline


def get_date_range(in_file, start_month, start_day, days_foward):
    temp_list = []
    current_month = start_month - 1
    try:
        current_month_data = in_file[start_month - 1]
    except:
        exit("Error Invalid Date Month Access")
    current_day = start_day
    for day in range(days_foward):
        try:
            temp_list.append({'month': current_month + 1, 'day': current_day, 'temp': current_month_data[current_day + 1]})
        except:
            exit("Error: Invalid Date Day Access")
        if current_day < (len(current_month_data) - 2):
            current_day += 1
        else:
            if current_month == 11:
                current_month = 0
                current_month_data = in_file[current_month]
                current_day = 1
            else:
                current_month += 1
                current_month_data = in_file[current_month]
                current_day = 1
    return temp_list


def get_formatted_forecast(input_list):
    return_list = []
    for day in input_list:
        return_list.append({'month': int(day['date']['month']), 'day': int(day['date']['day']), 'temp': int(day['high']['fahrenheit'])})
    return return_list


def get_normal_data(file_name, station_id):
    input_file = open(file_name, "r")
    data = read_data_lines(input_file, station_id)
    return data


def get_forecast_line(in_norm_line, in_zip):
    """
    Returns formatted forecasted temp line from Wunderground API for given zip code.

    :param in_norm_line:
    :param in_zip:
    :return:
    """
    live_request = requests.get("http://api.wunderground.com/api/" + WUNDERGROUND_KEY + "/forecast10day/q/" + in_zip + ".json")
    forecast_list = live_request.json()['forecast']['simpleforecast']['forecastday']
    formatted_forecast = get_formatted_forecast(forecast_list)

    fore_line = []
    for day in in_norm_line:
        status = 0
        for entry in formatted_forecast:
            if entry['day'] == day['day'] and entry['month'] == day['month']:
                fore_line.append(entry)
                status = 1
        if status == 0:
            fore_line.append(None)
    return fore_line


def get_station_id_zip(in_file, zip_code):
    for line in in_file:
        if line.split(",")[5] == str(zip_code):
            return line.split(",")[0]


def get_normal_locale(zip_code):
    inputf = open("STATION_LIST.csv", "r")
    station_id = get_station_id_zip(inputf, zip_code)
    if station_id is not None:
        return station_id
    else:
        exit("Error: Normal Temp Zip Code Invalid")
        exit(1)


def get_forecast_locale(zip_code):
    inputf = open("STATION_LIST.csv", "r")
    if get_station_id_zip(inputf, zip_code) is not None:
        return zip_code
    else:
        exit("Error: Forecast Temp Zip Code Invalid")


def get_match_line(data, forecast_line):
    return_line = []
    comp_date = get_date_range(data, 1, 1, 365)
    for point in forecast_line:
        best_match = None
        best_diff = None
        if point is not None:
            for temp in comp_date:
                diff = abs(point['temp'] - temp['temp'])
                if best_diff is None or best_diff > diff:
                    best_diff = diff
                    best_match = temp
        return_line.append(best_match)
    return return_line


def readout_print(norm_line, fore_line, match_line):
    print("Output for Zip Codes:")
    print("Normal Temp: %s, Forecast Temp: %s" % (used_real_nZip, used_real_fZip))
    output_table = PrettyTable(['Date', 'Norm', 'Foer', 'Diff', 'Comper'])
    for line in range(len(norm_line)):
        date = datetime.date(2000, norm_line[line]['month'], norm_line[line]['day'])
        if fore_line[line] is not None:
            comp_date = datetime.date(2000, match_line[line]['month'], match_line[line]['day'])
            temp_diff = int(round(fore_line[line]['temp'] - norm_line[line]['temp']))
            output_table.add_row([date.strftime("%m/%d"), str(norm_line[line]['temp']), str(fore_line[line]['temp']), temp_diff, comp_date.strftime("%m/%d")])
        else:
            output_table.add_row([date.strftime("%m/%d"), str(norm_line[line]['temp']), '-', '-', '-'])
    print(output_table)


parser = argparse.ArgumentParser()
parser.add_argument("-zip", help="increase output verbosity")
parser.add_argument("-nzip", help="increase output verbosity")
parser.add_argument("-fzip", help="increase output verbosity")
parser.add_argument("-date", help="increase output verbosity")
parser.add_argument("-num", help="increase output verbosity")
args = parser.parse_args()

fore_zip = args.fzip
normal_zip = args.nzip
joint_zip = args.zip

start_day = datetime.datetime.today().day
start_month = datetime.datetime.today().month
date_extend = 10

if args.date is not None:
   try:
        pieces = str(args.date).split("/")
        if len(pieces) == 2:
            start_month = int(pieces[0])
            start_day = int(pieces[1])
        else:
            exit("Error: Invalid Dates | Format mm/day")
   except:
    exit("Error: Invalid Dates | Format mm/day")

if joint_zip is None:
    if fore_zip is not None:
        if normal_zip is None:
            exit("Syntax Error: Missing Normal Zip Args")

    if normal_zip is not None:
        if fore_zip is None:
            exit("Syntax Error: Missing Forecast Zip Args")

if joint_zip is not None:
    normal_id = get_normal_locale(joint_zip)
    forecast_zip = get_forecast_locale(joint_zip)
    used_real_fZip = joint_zip
    used_real_nZip = joint_zip
else:
    normal_id = get_normal_locale(normal_zip)
    forecast_zip = get_forecast_locale(fore_zip)
    used_real_fZip = fore_zip
    used_real_nZip = normal_zip

if args.num is not None:
    try:
        date_extend = int(args.num)
        if date_extend < 1:
            exit("Error: Invalid Date Extend")
    except:
        exit("Error: Invalid Date Extend")

used_real_month = start_month
used_real_day = start_day

normal_data = get_normal_data("dly-tmax-normal.txt", normal_id)
normal_line = get_date_range(normal_data, start_month, start_day, date_extend)
forecast_line = get_forecast_line(normal_line, forecast_zip)
match_line = get_match_line(normal_data, forecast_line)
readout_print(normal_line, forecast_line, match_line)