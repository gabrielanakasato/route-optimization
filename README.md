<h1 align="center">OptRotas</h1>

<p align="center">  
<b>OptRotas</b> is an app that tries to find the <b>best route</b> given <b>locations</b> and <b>period of time</b>.
</p>
<p align="center">  
It was created as the final project for the Ironhack Data Analytics Bootcamp.
</p>
</p>
<p align="center">  
The live app is available <a href="https://optrotas.herokuapp.com/" target="__blank">here</a> (INACTIVE).
</p>


## Table of Content
- [Motivation](#motivation)
- [Project Status](#project-status)
- [Features](#features)
- [Streamlit Demo](#streamlit-demo)
- [Technologies](#technologies)
- [Issues](#issues)
- [To-Do](#to-do)

## Motivation
When the COVID-19 appeared, people from all around the world had to change their daily habits to adjust to the new reality. One of them was the online shopping, which had a huge increase. This also greatly impacted small businesses that depend on sales only in physical stores, encouraging many of them to join the e-commerce.

## Project Status
:white_check_mark: Complete

## Features
- [x] Input for number of deliveries
- [x] Input for addresses
- [x] Input for number of vehicles
- [x] Input for maximum travel time
- [x] Map showing the route sequence by vehicle
- [X] Input the Distance Matrix API key

## Streamlit Demo
![Demo v0](https://github.com/gabrielanakasato/route-optimization/blob/main/midia/route-optimization-demo.gif)

## Technologies
- Python 3.8
- [Streamlit](https://www.streamlit.io/)
- [Selenium](https://selenium-python.readthedocs.io/)
- [Distance Matrix API](https://developers.google.com/maps/documentation/distance-matrix/overview)
- [OR-Tools](https://developers.google.com/optimization)
- [Folium](https://python-visualization.github.io/folium/)

## Run this App Locally - Windows
```
git clone https://github.com/gabrielanakasato/route-optimization.git
```
To run this app, it is required the [Chrome Driver](https://chromedriver.chromium.org/downloads). So, download it and move it to the folder `scr` or change its path in the file `params.py`.
```
cd route-optimization/scr
streamlit run main.py
```

## Issues
- The higher the number of locations and the lower the number of vehicles, the longer it takes to find the solution.

## To-Do
- [x] Write docstrings
- [X] Add a text insert for the API key, so it is be possible to deploy it
- [X] Deploy it
- [ ] Translate to English

## Improvements
- Refactor the code
