# FORK: https://github.com/swishderzy/ForexCalendar

# https://www.forexfactory.com/calendar.php?week=jan1.2007
# https://www.metalsmine.com/calendar.php?week=jan1.2007
# https://www.energyexch.com/calendar.php?week=jan1.2007

from selenium import webdriver
import datetime, argparse, sys
from babel.dates import format_date, format_datetime, format_time
from bs4 import BeautifulSoup
import requests
import logging
import csv
import re

VERSION = '1.0'

BASE_URLS = {
    "forexfactory": "https://www.forexfactory.com/", 
    "metalsmine": "https://www.metalsmine.com/", 
    "energyexch": "https://www.energyexch.com/"
    }


def makeHeaderLine(base_url):
    # write header line, different from FIELDS as it's being used in DOM lookup
    header_fields = ["datetime", "currency", "impact", "event", "actual", "forecast", "previous", "state"]
    with open(f"calendar_data/{base_url.split('.')[1]}_historical.csv", "a", newline="\n") as f:
        csv.writer(f).writerow(header_fields)


def setLogger():
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='logs/log-historical.txt',
                    filemode='w')
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def getEconomicCalendar(base_url, startlink, endlink):
    # write to console current status
    logging.info("Scraping data for link: {}".format(startlink))    
    # run webdriver Chrome
    driver = webdriver.Chrome('./chromedriver')  # Optional argument, if not specified will search path.
    driver.implicitly_wait(30)
    driver.get(base_url + startlink)
    # make "Soup" from driver
    soup = BeautifulSoup(driver.page_source, "lxml")
    # get and parse table data, ignoring details and graph
    table = soup.find("table", class_="calendar__table")

    # From original repository:
    # do not use the ".calendar__row--grey" css selector (reserved for historical data)
    # trs = table.select("tr.calendar__row.calendar_row")

    # As we're fetching a lot of past data, calendar__row--grey is now included
    trs = table.select("tr.calendar__row.calendar__row--grey")
    
    # some rows do not have a date (cells merged)
    curr_year = startlink[-4:]
    curr_date = ""
    curr_time = ""

    lookup_fields = ["date","time","currency","impact","event","actual","forecast","previous"]
    for tr in trs:
        # fields may mess up sometimes, see Tue Sep 25 2:45AM French Consumer Spending
        # in that case we append to errors.csv the date time where the error is
        try:
            for field in lookup_fields:
                data = tr.select("td.calendar__cell.calendar__{}.{}".format(field,field))[0]
                # print(data)
                if field=="date" and data.text.strip()!="":
                    curr_date = data.text.strip()
                elif field=="time" and data.text.strip()!="":
                    # time is sometimes "All Day" or "Day X" (eg. WEF Annual Meetings)
                    if data.text.strip().find("Day")!=-1:
                        curr_time = "12:00am"
                    else:
                        curr_time = data.text.strip()
                elif field=="currency":
                    currency = data.text.strip()
                elif field=="impact":
                    # when impact says "Non-Economic" on mouseover, the relevant
                    # class name is "Holiday", thus we do not use the classname
                    impact = data.find("span")["title"]
                elif field=="event":
                    event = data.text.strip()
                elif field=="actual":
                    actual = data.text.strip()
                    #state = re.findall("class=\"calendar__cell calendar__actual actual\"><span class=\"(.*)\">.*</span></td>", str(data))
                    if "better" in str(data):
                        state = "better"
                    elif "worse" in str(data):
                        state = "worse"
                    else:
                        state = "None"
                elif field=="forecast":
                    forecast = data.text.strip()
                elif field=="previous":
                    previous = data.text.strip()

            dt = datetime.datetime.strptime(",".join([curr_year,curr_date,curr_time]),
                                            "%Y,%a%b %d,%I:%M%p")
            #sys.exit(curr_year+' '+curr_date+' '+curr_time)
            with open(f"calendar_data/{base_url.split('.')[1]}_historical.csv", "a", newline="\n") as f:
                csv.writer(f).writerow([str(dt), currency, impact, event, actual, forecast, previous, state])
        except:
            with open("logs/errors.csv","a") as f:
                csv.writer(f).writerow([curr_year,curr_date,curr_time])

    # get start and end date data from links
    start_year, end_year = int(startlink.split("=")[1].split(".")[1]), int(endlink.split("=")[1].split(".")[1])  # fetching 4-digit year
    start_month, end_month = startlink.split("=")[1][:3], endlink.split("=")[1][:3]  # fetching 3-digit month
    start_day = int(startlink.split("=")[1][3]) if startlink.split("=")[1][4] == "." else int(startlink.split("=")[1][3:4])  # if [4] == ".", day counter is single-digit
    end_day = int(endlink.split("=")[1][3]) if endlink.split("=")[1][4] == "." else int(endlink.split("=")[1][3:4])  # if [4] == ".", day counter is single-digit
    
    # exit recursion when end date has been reached / overstepped
    if start_year == end_year and start_month==end_month and start_day >= end_day:
        print("Successfully retrieved data")
        sys.exit(2)
    else:
        # otherwise, get the link for the next week and follow
        follow = soup.select("a.calendar__pagination.calendar__pagination--next.next")
        follow = follow[0]["href"]
        driver.close()
        getEconomicCalendar(base_url, follow, endlink)

if __name__ == "__main__":
    """
    Run this using the command "python `script_name`.py --source <forexfactory, metalsmine, energyexch>
    """
    setLogger()
    # Initiate args parser with description
    parser = argparse.ArgumentParser(
        description='This program will fetch the economic calendar from one of the supported sources \
                    (forexfactory, metalsmine, energyexch) for a specified timeframe. Example: python <script_name>.py --source forexfactory')
    # add desired "version", "source", "startlink" and "endlink" parameter
    parser.add_argument("-V", "--version", 
        help="Show program version.", 
        action="store_true")
    parser.add_argument("-S", "--source", 
        help="Use --source / -s parameter to set one of the following sources for the calendar: forexfactory, metalsmine, energyexch.")
    parser.add_argument("-s", "--start", 
        help="Use --start / -s to define start date in the format [jan-dec][1-31].[yyyy]")
    parser.add_argument("-e", "--end", 
        help="Use --end / -e to define end date in the format [jan-dec][1-31].[yyyy]")
    args = parser.parse_args()
    if args:
        # Check for --version or -V
        if args.version:
            print("This is myprogram version 1.0")
        # Check for --source or -S
        elif args.source:
            logging.info(f"Setting base URL to: {BASE_URLS[args.source]}")
            makeHeaderLine(BASE_URLS[args.source])
            if args.start:
                # TODO: no parameter format check
                start_date = args.start
            else:
                # no paramter given, using beginning of records on given source sites
                start_date = 'jan1.2007'
            if args.end:
                # TODO: no parameter format check
                end_date = args.end
            else:
                # make sure we're working on en_US locale for getting the month
                date = datetime.datetime.now()
                month = format_date(date, locale='en')[:3].lower()
                # remove leading 0 from day manually; lots of researched suggestions are python version / os dependent.
                day = date.strftime("%d") if date.strftime("%d")[0] != "0" else date.strftime("%d")[1]
                # generate endlink from current EN datetime.
                end_date = month + day + '.' + date.strftime("%Y")
                print(f"No end date parameter passed. Using current date: {end_date}")

            # get calendar with given source and start + end date
            getEconomicCalendar(BASE_URLS[args.source], "calendar.php?week="+start_date, "calendar.php?week="+end_date)

        else:
            print("")
            print ("--- REQUIRED PARAMETER NOT GIVEN ---")
            print("")
            print ("(1)(REQUIRED) Use --source / -S parameter to set one of the following sources for the calendar: forexfactory, metalsmine, energyexch.")
            print("Example: python 'script_name'.py --source forexfactory")
            print("")
            print ("(2)(OPTIONAL) Use --start / -s and --end / -e to define start and end date in the format [jan-dec][1-31].[yyyy]")
            print("Example: python 'script_name'.py --source forexfactory --start jan1.2007 --end nov2.2020")
            print("If not given, will take jan1.2007 until current date.")
            print("")
    else:
        print ("ERROR parsing parameters.")
        sys.exit(2)
