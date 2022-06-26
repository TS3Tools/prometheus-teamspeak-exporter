#!/usr/bin/env python3

import os
import sys
import timeit
import requests
import re

from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

# Environment variables
ENABLE_DEBUG = os.getenv('ENABLE_DEBUG', False)
TEAMSPEAK_API_ENDPOINT_BASE_URL = os.getenv('TEAMSPEAK_API_ENDPOINT_BASE_URL', 'http://localhost:10080')
TEAMSPEAK_API_KEY = os.getenv('TEAMSPEAK_API_KEY')
PROMETHEUS_GAUGE_DIRECTORY = os.getenv('PROMETHEUS_GAUGE_DIRECTORY', '/var/lib/prometheus/gauges/')
PROMETHEUS_GAUGE_FILE_NAME = os.getenv('PROMETHEUS_GAUGE_FILE_NAME', 'teamspeak')
REQUEST_TIMEOUT_IN_SECONDS = os.getenv('REQUEST_TIMEOUT_IN_SECONDS', 10)

# Where all metrics will be temporarly saved
registry = CollectorRegistry()

# Gauges
gauge_teamspeak_scrape_collector_duration_seconds = Gauge(name="teamspeak_scrape_collector_duration_seconds",
    documentation="information about the scraping duration in seconds",
    labelnames=["endpoint", "key"],
    registry=registry
)

gauge_teamspeak_hostinfo = Gauge(name="teamspeak_hostinfo",
    documentation="information about the teamspeak host",
    labelnames=["endpoint", "key"],
    registry=registry
)

gauge_teamspeak_instanceinfo = Gauge(name="teamspeak_instanceinfo",
    documentation="information about the teamspeak instance",
    labelnames=["endpoint", "key"],
    registry=registry
)

gauge_teamspeak_logview = Gauge(name="teamspeak_logview",
    documentation="specific information from the instance log",
    labelnames=["endpoint", "key"],
    registry=registry
)

gauge_teamspeak_virtualserver_serverrequestconnectioninfo = Gauge(name="teamspeak_virtualserver_serverrequestconnectioninfo",
    documentation="connection information about teamspeak virtual servers",
    labelnames=["endpoint", "virtualserver_id", "key"],
    registry=registry
)

gauge_teamspeak_virtualserver_serverinfo = Gauge(name="teamspeak_virtualserver_serverinfo",
    documentation="server information about teamspeak virtual servers",
    labelnames=["endpoint", "virtualserver_id", "key"],
    registry=registry
)

def debug_message(message = ""):
    if ENABLE_DEBUG:
        print(message)

# Runtime start
runtime_start = timeit.default_timer()

debug_message(f"Collecting metrics from {TEAMSPEAK_API_ENDPOINT_BASE_URL}...")
debug_message("Checking if an API key is provided.")

# Check if an API key is provided
if bool(TEAMSPEAK_API_KEY) == False:
    debug_message("Error: You need to provide an API key. Please set the environment variable 'TEAMSPEAK_API_KEY'.")
    sys.exit()

def webquery_api_request(query = "", payload = {}):
    """
    Performs a HTTP GET request against the TeamSpeak
    WebQuery API and returns the reponse of the API.
    """
    try:
        response = requests.get(
            f"{TEAMSPEAK_API_ENDPOINT_BASE_URL}/{query}",
            headers={'x-api-key': f"{TEAMSPEAK_API_KEY}"},
            timeout=REQUEST_TIMEOUT_IN_SECONDS,
            params=payload
        )
    except requests.ConnectionError as e:
        raise Exception(e)

    return response

##
## HOSTINFO
##
# Check once if the provided WebQuery API endpoint is reachable or not
response = webquery_api_request("hostinfo")
if bool(response) == False:
    debug_message(f"Error: Your TeamSpeak WebQuery API '{TEAMSPEAK_API_ENDPOINT_BASE_URL}' is not reachable. Please double-check your environment variable 'TEAMSPEAK_API_ENDPOINT_BASE_URL'.")
    sys.exit()

response = response.json()
if response['status']['code'] == 0:
    for key in response['body'][0]:
        gauge_teamspeak_hostinfo.labels(TEAMSPEAK_API_ENDPOINT_BASE_URL, key).set(response['body'][0][key])
else:
    debug_message(f"Skipping metric collection of 'hostinfo'. API Error: {response['status']['message']}")

##
## INSTANCEINFO
##
response = webquery_api_request("instanceinfo").json()
if response['status']['code'] == 0:
    for key in response['body'][0]:
        gauge_teamspeak_instanceinfo.labels(TEAMSPEAK_API_ENDPOINT_BASE_URL, key).set(response['body'][0][key])
else:
    debug_message(f"Skipping metric collection of 'instanceinfo'. API Error: {response['status']['message']}")

##
## LICENSE
##

ending_date_pattern = re.compile("ending date")
logview_payload_begin_pos = 0
license_ending_date = ""
while license_ending_date == "":
    logview_payload = {
        "lines": 100,
        "reverse": 1,
        "instance": 1,
        "begin_pos": logview_payload_begin_pos
    }

    try:
        response = webquery_api_request("logview", logview_payload)
    except Exception as e:
        print(e)
        continue

    response = response.json()
    if response['status']['code'] == 0:
        for line in response['body']:
            if "last_pos" in line:
                print(line["last_pos"])

            if "l" in line:
                if ending_date_pattern.match(line["l"]):
                    print(line["l"])
                    license_ending_date = False

        logview_payload_begin_pos = logview_payload_begin_pos + 100
        #for key in response['body'][0]:
        #    gauge_teamspeak_logview.labels(TEAMSPEAK_API_ENDPOINT_BASE_URL, key).set(response['body'][0][key])
    else:
        debug_message(f"Skipping metric collection of 'logview'. API Error: {response['status']['message']}")

##
## COLLECT VIRTUALSERVER SPECIFIC METRICS
##
debug_message("Collecting list of all virtualservers...")

response = webquery_api_request("serverlist").json()
if response['status']['code'] == 0:
    teamspeak_virtualserver_list = response['body']
else:
    teamspeak_virtualserver_list = []
    debug_message(f"Skipping metric collection of 'serverlist'. API Error: {response['status']['message']}")

for virtualserver in teamspeak_virtualserver_list:
    for key in virtualserver:
        if key == "virtualserver_id":
            virtualserver_id = virtualserver[key]

            ##
            ## VIRTUAL SERVER: SERVER REQUEST CONNECTION INFO
            ##
            debug_message(f"Collecting connection info metrics for virtualserver id {virtualserver_id}...")

            response = webquery_api_request(f"{virtualserver_id}/serverrequestconnectioninfo").json()
            if response['status']['code'] == 0:
                for key in response['body'][0]:
                    gauge_teamspeak_virtualserver_serverrequestconnectioninfo.labels(TEAMSPEAK_API_ENDPOINT_BASE_URL, virtualserver_id, key).set(response['body'][0][key])
            else:
                debug_message(f"Skipping metric collection of 'serverrequestconnectioninfo'. API Error: {response['status']['message']}")
            
            ##
            ## VIRTUAL SERVER: SERVERINFO
            ##
            debug_message(f"Collecting serverinfo metrics for virtualserver id {virtualserver_id}...")

            response = webquery_api_request(f"{virtualserver_id}/serverinfo").json()
            if response['status']['code'] == 0:
                for key in response['body'][0]:
                    if key == "virtualserver_status":
                        if response['body'][0][key] == "online":
                            value = True
                        else:
                            value = False
                    elif key == "virtualserver_version":
                        _, _, value = response['body'][0][key].replace(']', '').split()
                        key = "virtualserver_version_build"
                    else:
                        # Convert values to float, if possible
                        # Unconvertable values will not be exported as metric
                        try:
                            value = float(response['body'][0][key])
                        except ValueError:
                            value = response['body'][0][key]

                    # Only try to export metrics, which are numbers
                    if isinstance(value, (bool, int, float)) == False:
                        continue

                    try:
                        gauge_teamspeak_virtualserver_serverinfo.labels(TEAMSPEAK_API_ENDPOINT_BASE_URL, virtualserver_id, key).set(value)
                    except ValueError:
                        pass
            else:
                debug_message(f"Skipping metric collection of 'serverinfo'. API Error: {response['status']['message']}")

# Runtime end
runtime_end = timeit.default_timer()
runtime_duration_in_seconds = runtime_end - runtime_start
try:
    gauge_teamspeak_scrape_collector_duration_seconds.labels(TEAMSPEAK_API_ENDPOINT_BASE_URL, "total").set(runtime_duration_in_seconds)
except ValueError:
    pass

debug_message(f"Scraping all metrics took {runtime_duration_in_seconds} seconds.")

# Save all metrics to a *.prom file
write_to_textfile(f"{PROMETHEUS_GAUGE_DIRECTORY}/{PROMETHEUS_GAUGE_FILE_NAME}.prom", registry)

debug_message("Script successfully finished")
