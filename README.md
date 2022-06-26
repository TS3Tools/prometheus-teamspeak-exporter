# Prometheus TeamSpeak Exporter

This Prometheus exporter allows you to collect metrics from all your TeamSpeak instances and virtual servers using the TeamSpeak WebQuery API, which was introduced on the 18th March 2020.

## Available Gauges (Metrics)

The exporter is currently providing the following metrics as gauges:

- `teamspeak_hostinfo`: information about the teamspeak host
    - instance uptime
    - virtualservers running in total
    - connection packets in total
    - total max. clients
    - total online clients
    - ...
- `teamspeak_instanceinfo`: information about the teamspeak instance
    - database version
    - max. total bandwidths
    - serverquery ban time
    - ...
- `teamspeak_virtualserver_serverrequestconnectioninfo`: connection information about teamspeak virtual servers
    - connection ping
    - connection packet loss
    - connection bytes received in total
    - connection bytes sent in total
    - connection bandwidth received in the last minute
    - connection bandwidth sent in the last minute
    - ...
- `teamspeak_virtualserver_serverinfo`: server information about teamspeak virtual servers
    - virtualserver autostart status
    - virtualserver status
    - virtualserver uptime
    - serverquery clients online counter
    - clients online counter
    - channels counter
    - ...

## Requirements

- Prometheus Server (to save the metrics)
- Grafana (optional to visualize the metrics)
- Python 3.x
- TeamSpeak Server 3.12.0 or newer
- TeamSpeak WebQuery API Key (see below for further information)

## TeamSpeak WebQuery API Key

The Python script is requesting the respective metrics from the TeamSpeak instance / virtual server using the WebQuery API. This API requires an API key.

Follow this wizard to create an API with the respective required permissions for this exporter:

1. Login to your TeamSpeak server using ServerQuery credentials (either via telnet (insecure) or SSH (secure))
2. Create a new full access API key: `apikeyadd scope=manage lifetime=0`
    - _lifetime_: lifetime of the token in days; default `14`, `0` means unlimited
    - For security reasons, you also could define a lifetime of the token for e.g. `90` days and then you need to renew the API key every 90 days.
    - TeamSpeak does unfortunately not allow to e.g. get the `serverlist` and `serverinfo` using the read-only scope `read` (state October 2021).
3. Note down your newly created API key (eg. `AQB8J1sfuvq4wFAFdo6rsfFq+jAQO9asz3zGq5X`)

## Installation

1. Clone the repository to either your Prometheus host (recommended, as this also directly checks the reachability of your WebQuery API endpoint) or to each TeamSpeak host
2. Install the Python requirements: `pip3 install -r requirements.txt`
3. Test the exporter manually: `ENABLE_DEBUG=True TEAMSPEAK_API_KEY='<YOUR_API_KEY>' [Additional Environment Variable(s)] ./prometheus-teamspeak-exporter.py`

## Supported Environment Variables

| Required | Variable | Default | Description |
| ---------| -------- | ------- | ----------- |
| Optional | ENABLE_DEBUG | `False` | Set to `True` to enable debugging messages |
| Optional | TEAMSPEAK_API_ENDPOINT_BASE_URL | `http://localhost:10080`  | Your TeamSpeak WebQuery API endpoint base URL |
| Required | TEAMSPEAK_API_KEY | _undefined_ | Your TeamSpeak WebQuery API key (see above) |
| Optional | PROMETHEUS_GAUGE_DIRECTORY | `/var/lib/prometheus/gauges/` | The directory, where the metrics will be saved |
| Optional | PROMETHEUS_GAUGE_FILE_NAME | `teamspeak` | The name of the file, in which the metrics will be saved (without `.prom` file extension) |
| Optional | REQUEST_TIMEOUT_IN_SECONDS | `10` | The time in seconds, when a WebQuery API request will timeout |

## Debugging

By default, the Python script is not printing any messages even when these would be errors. The reason for this is to avoid spamming any log files and also to e.g. avoid frozen messages (emails which can not be delivered) on the host system.

If something is not working, you can enable debugging by simply setting the environment variable `ENABLE_DEBUG` to `True`:

`ENABLE_DEBUG=True TEAMSPEAK_API_KEY='<YOUR_API_KEY>' [Additional Environment Variable(s)] ./prometheus-teamspeak-exporter.py`

## Refs

- Prometheus Client Python: https://github.com/prometheus/client_python
- Textfile Collector: https://github.com/prometheus/node_exporter#textfile-collector
