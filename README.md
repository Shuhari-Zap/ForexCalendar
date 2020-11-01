# ForexCalendar
The economic calendar of Foreign Exchange from forexfactory.com, metalsmine.com and energyexch.com with the state of the actual value compared to the forecasted ("better" or "worse").

Usage:

1- Set up Selenium with a driver of your choice (default=Chrome 87 (beta)). This was added as the source sites' CloudFlare setup requires a an actual browser session. (workarounds with requests.Session() as well as CfScrape (https://pypi.org/project/cfscrape/) have not worked out.

2- Change the dates as you please at the end of the code.

3- Run this using the command "python `script_name`.py

4- Output has been changed to be written into CSV made with source name (iteration over all three sources)


Dependencies:
- BeautifulSoup
- Selenium WebDriver
- requests
- datetime
- logging
- csv
- re

Any improvements and feedbacks are welcome.

Many thanks to SwishDerzy for the base code.
