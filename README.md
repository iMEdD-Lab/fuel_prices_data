# Greek Fuel Prices Observatory Tracker
A data pipeline that utilizes python and github actions to automatically downloads the prices of fuel that are uploaded on the website of the Greek ministry of Development. It downloads the pdf files using python, scrapes the tables and updates a .csv file that contains the entire dataset from 2017. 

Fuel types that are tracked:
1. Diesel
2. Unleaded 100
3. Unleaded 95
4. Autogas

