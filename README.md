
Belle2 ECL monitoring by uSOP 
=============================

This is repository for B2 ECL monitoring composed by client and server modules.

Each uSOP board runs a collectd (http://www.collectd.org) daemon that gather
system metrics and EPICS PV (by a custom Python plugin)

Metrics are sent to a web service (web2influxdb) that runs on a dedicated server;
historical archive are also provided by InfluxDB (https://influxdata.com) and
data are displayed by Grafana web application (http://www.grafana.org)

Repository synced with https://gitlab.desy.de/gennaro.tortone/b2-eclmon

Client modules (uSOP side)
--------------------------
- collectd Python plugin
- collectd configuration file

Server modules (server side)
----------------------------
- web2influxdb
- influxdb configuration file

Management URLs (server side)
-----------------------------
- Grafana
   - http://server-address:3000

- InfluxDB - database UI
   - http://server-address:8083

- InfluxDB - graphite
   - socket://server-address:2003
