# -*- coding: utf-8 -*-
"""
Created on Tue Oct 23 15:13:01 2018

@author: Hung Mach
"""
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyA7Qsam0WsI3_eVExTgdKFdSbmDAQ_j3NM"

import geocoder
import requests

address = '8882 Dakota Ave, Garden Grove, CA'

keyword = "counseling OR therapist OR psychiatrist"
g = geocoder.google(address, key='AIzaSyA7Qsam0WsI3_eVExTgdKFdSbmDAQ_j3NM')
print(g.latlng)
latlng = g.latlng
location = "{},{}".format(latlng[0], latlng[1])
print(location)
key = "AIzaSyACC15SxgdpnLrFn9ZHBkbWEuJrZHCEDsI"
URL2 = "https://maps.googleapis.com/maps/api/place/textsearch/json?location={}&query={}&key={}".format(location,keyword,key)
print(URL2)
r2 = requests.get(URL2)
if r2.status_code == 200:
    first_output = r2.json()
else:
    print("Sorry, I'm having trouble doing that right now. Please try again later.")
print(first_output)