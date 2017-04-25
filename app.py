#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    if req.get("result").get("action") != "yahooWeatherForecast" or req.get("result").get("action") != "yahooWeatherCondition":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data,req)
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    degree = parameters.get("temperature")
    if city is None:
        return None
    
    #if degree is "celsius":
        #u="c"
    #else:
        #u="f" AND u='" + u + "'
    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data,req):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    result = req.get("result")
    parameters = result.get("parameters")
    condition=parameters.get("Condition")
    
    winddetail = channel.get('wind')
    atmosphere = channel.get('atmosphere')
    sun = channel.get('astronomy')
    if (location is None) or (item is None) or (units is None):
        return {}

    cond = item.get('condition')
    if cond is None:
        return {}

    # print(json.dumps(item, indent=4))
    if req.get("result").get("action") == "yahooWeatherForecast":
        speech = "The weather in " + location.get('city') + ": " + cond.get('text') + \
                 ", the temperature is " + cond.get('temp') + " " + units.get('temperature')
            
    if req.get("result").get("action") == "yahooWeatherCondition":
        if condition == "windspeed":
            speech = "The windspeed is " + winddetail.get('speed') + " " + units.get('speed') +" in " + location.get('city')
        if condition == "direction":
            speech = "The direction is " + winddetail.get('direction') + " " +" in " + location.get('city')
        if condition == "humidity":
            speech = "The humidity is " + atmosphere.get('humidity') + " " + units.get('speed') +" in " + location.get('city')
        if condition == "pressure":
            speech = "The pressure is " + atmosphere.get('pressure') +" in " + location.get('city')
        if condition == "sunrise":  
            speech = "The Sunrise is at" + sun.get('sunrise') +" in " + location.get('city')
        if condition == "sunset":
            speech = "The Sunset is at" + sun.get('sunset') +" in " + location.get('city')
        
    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
