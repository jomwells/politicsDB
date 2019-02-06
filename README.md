# politicsDB - Python news article scraper and database script
(part of) A Python/Flask/SQL application for scraping the internet for news articles mentioning UK politicians and/or political parties, and saving these to a searchable SQL database (for use with a Flask Web Server - not included) along with references to all mentions.

## This code relies on the database (JSON file) of politicans names, websites and images provided by the government [here](http://eldaddp.azurewebsites.net/commonsmembers.json?_pageSize=2000&_page=0&_view=members)
Please note - this file is now outdated (as of the 2017 GE) however the code functions properly 

**This is only part of the application (which is work in progress), this provides no mechanism for viewing the contents of the generated site.db file, or searching for a particular politicans, this is achieved through a custom Flask web server.** However, the methods used in update_database.py could be adapted for any form of web article scraping
