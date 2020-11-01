# FORK: https://github.com/swishderzy/ForexCalendar

# https://www.forexfactory.com/calendar.php?week=jan1.2007
# https://www.metalsmine.com/calendar.php?week=jan1.2007
# https://www.energyexch.com/calendar.php?week=jan1.2007

from selenium import webdriver

from bs4 import BeautifulSoup
import requests
import datetime
import logging
import csv
import re


FIELDS = ["date", "time", "currency", "impact", "event", "actual", "forecast", "previous"]
BASE_URLS = ["https://www.forexfactory.com/", "https://www.metalsmine.com/", "https://www.energyexch.com/"]


def makeHeaderLine(fields):
    header_line = ""
    for field in fields:
        header_line = header_line + field + ","
    print(header_line[:-1])


def setLogger():
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='logs_file',
                    filemode='w')
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def getEconomicCalendar(base_url, fields, startlink, endlink):
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
    for tr in trs:
        # fields may mess up sometimes, see Tue Sep 25 2:45AM French Consumer Spending
        # in that case we append to errors.csv the date time where the error is
        try:
            for field in fields:
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
            with open(f"{base_url.split('.')[1]}.csv", "a", newline="\n") as f:
                csv.writer(f).writerow([str(dt), currency, impact, event, actual, forecast, previous, state])
        except:
            with open("errors.csv","a") as f:
                csv.writer(f).writerow([curr_year,curr_date,curr_time])

    # exit recursion when last available link has reached
    if startlink==endlink:
        logging.info("Successfully retrieved data")
        return

    # get the link for the next week and follow
    follow = soup.select("a.calendar__pagination.calendar__pagination--next.next")
    follow = follow[0]["href"]
    driver.close()
    getEconomicCalendar(base_url, FIELDS, follow, endlink)

if __name__ == "__main__":
    """
    Run this using the command "python `script_name`.py >> `output_name`.csv"
    """
    setLogger()
makeHeaderLine(FIELDS)
for base_url in BASE_URLS:
    getEconomicCalendar(base_url, FIELDS,"calendar.php?week=jan1.2007","calendar.php?week=nov02.2020")
