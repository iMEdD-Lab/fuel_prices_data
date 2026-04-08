# Greek Fuel Prices Observatory Tracker
The Greek Fuel Prices Observatory tracker was created to gather, analyse and visualize the pdf files of the observatory of liquid fuel prices of the Greek Ministry of Development. It was created in April 2026, after the upheaval created in the oil prices because of the closure of the strait of Hormuz, after the joint American-Israeli attacks on Iran. 

In this public repository are the data files of a pipeline that utilizes Python and Github Actions to download the latest data from the observatory, which then are fed into a Google Sheets file automatically, using a script, and then visualized through Datawrapper, and published in an article on the website of iMEdD. 

The repository contains three directory:
1. national
2. prefectures
3. datawrapper_api 

**National**
This directory contains only one file. The prices_of_petrol.csv, which contains daily data on the national average price/liter of different fuel types. The earliest data is on the 14th of March 2017, and the .csv is updated daily, except on the weekends, when the ministry doesn't publish data. 

Fuel types that are tracked:
1. Diesel
2. Unleaded 100
3. Unleaded 95
4. Autogas

**Prefectures**
In the prefecture directory there are two subdirectories that contain a different set of the same data on the prefecture prices. 

The subdirectory "latest_only" contains a .csv that has only the data from the latest .pdf that was published on the ministry's website. 

The subdirectory "update_master" contains three .csv files:
1. master_pref_old.csv -> contains the data from the start of the data releases on the ministry's website, up until the 23rd of March 2026.
2. master_pref_upd.csv -> this is the file that gets updated via our Python code that is run in a private repo.
3. pref_2026.csv -> copy of the "master_pref_upd.csv" that contains only the data from the 1st of January 2026.

**Datawrapper_api**
In this directory we have stored dozens of .png files that visualize the average price of each fuel type for each prefecture. The images are updated daily via a Python script in our private repo that utilises Datawrapper API to update the charts automatically, then downloads the image file and saves it to the "temp_images" subdirectory. 
