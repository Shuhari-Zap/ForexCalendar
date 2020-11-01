import requests
import logging
import csv


def configureLogger():
        logging.basicConfig(level=logging.INFO, filename='log-weekly.txt', 
            format='%(asctime)s - %(levelname)s: %(message)s', filemode='w')
        console = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)


class WeeklyJsonCalendar():
    def __init__(self, calendar_type):
        if calendar_type in ['ff', 'ee', 'mm']:
            # write header line
            header_fields = ["datetime", "currency", "impact", "event", "actual", "forecast", "previous", "state"]
            with open(f"{calendar_type}_weekly.csv", "a", newline="\n") as f:
                csv.writer(f).writerow(header_fields)
            # fetch JSON    
            self.BASE_URL = 'https://cdn-nfs.faireconomy.media/'+calendar_type+'_calendar_thisweek.json'
            logging.info("Fetching weekly calendar JSON: " + self.BASE_URL)
            response = requests.get(self.BASE_URL)        
            # Response Code 200
            if response.status_code == 200:
                self.calendar_json = response.json()
                for entry in self.calendar_json:
                    with open(f"{calendar_type}_weekly.csv", "a", newline="\n") as f:
                        if 'actual' in entry:
                            csv.writer(f).writerow([entry['date'], entry['country'], entry['impact'], entry['title'], entry['actual'], entry['forecast'], entry['previous'], ''])
                        else:
                            csv.writer(f).writerow([entry['date'], entry['country'], entry['impact'], entry['title'], '', entry['forecast'], entry['previous'], ''])

                    print(f"---------- Date: {entry['date']} ----------")
                    print(f"Tile: {entry['title']}")
                    print(f"Country: {entry['country']}")
                    print(f"Impact: {entry['impact']}")
                    print(f"Forecast: {entry['forecast']}")
                    print(f"Previous: {entry['previous']}")
                    if 'actual' in entry:
                        print(f"Actual: {entry['actual']}")

            else:
                logging.error("ERROR fetching weekly calendar JSON. Code: " + response.status_code)
                response.raise_for_status()
        else:
            logging.error("ERROR: Given calendar type not recognised. Input:" + str(calendar_type))


if __name__ == "__main__":
    configureLogger()
    for calendar_type in ['ff', 'ee', 'mm']:
        print(f"Calendar Type: {calendar_type}")
        ff_calendar = WeeklyJsonCalendar(calendar_type)
        # print(ff_calendar.raw_calendar)
