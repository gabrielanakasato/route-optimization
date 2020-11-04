<h1 align="center">OptRotas</h1>

<p align="center">  
OptRotas is an app that tries to find the best route given locations and period of time
</p>
<p align="center">  
It was created as the final project for the Ironhack Data Analytics Bootcamp.
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
:construction: In Progress :construction:

## Features
- [x] Input for number of deliveries
- [x] Input for locations
- [x] Input for number of vehicles
- [x] Input for maximum travel time
- [x] Map showing the route sequence by vehicle

## Streamlit Demo
To-Do

## Technologies
- Python
- Streamlit
- Selenium
- Distance Matrix API - Google Maps
- OR-Tools
- Folium

## Issues
- Since the Distance Matrix API is a paid one, it is unfeasible to host it and make it available online for everyone to use it.
- Error appears when there is no coordinates of "Sua localização".
- The higher the number of locations and the lower the number of vehicles, the longer it takes to find the solution.

## To-Do
- [x] Write docstrings
- [ ] Insert a "drop file" section for the API key, so it would be possible to host it
- [ ] Translate to English

## Improvements
- Refactor the code
