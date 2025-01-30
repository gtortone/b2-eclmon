#!/usr/bin/env python3

import os
import collectd
import signal
import epics
import yaml

"""
example of metric name:
    collectd.usop.S1B.1.humidity
"""

os.environ["PYEPICS_LIBCA"] = "/opt/epics/lib/linux-arm/libca.so"

debug = False

doc = {}
pvs = []
pvstate = {}

def onConnectionChange(pvname=None, conn=None, **kws):
   collectd.info('b2-eclmon: PV connection status changed: %s %s' % (pvname,  repr(conn)))
   pvstate[pvname] = conn

def init_callback():
 
   global debug
   global doc, pvs, pvstate

   signal.signal(signal.SIGCHLD, signal.SIG_DFL)

   stream = open('/opt/collectd-plugins/b2-ecl-sec.yaml', 'r')

   try:
      doc = yaml.safe_load(stream)
   except exc:
      collectd.info("b2-eclmon: error in configuration file: %s" % (exc))

   if debug:
      collectd.info("init - dump config file: %s" % (yaml.dump(doc)))

   for pv in doc:
      collectd.info("%s" % pv)
      pvs.append(epics.PV(pv, connection_callback=onConnectionChange))

   for pv in pvs:
      pvstate[pv.pvname] = False

   collectd.info("b2-eclmon: plugin started")

   stream.close()

def read_callback(data=None):

   global debug
   global doc, pvs, pvstate
   
   # EPICS PVs

   for pv in pvs:

      if pv.pvname in pvstate:
         if pvstate[pv.pvname] == True:		# PV is connected

            pv.get()

            if debug:
               collectd.info("b2-eclmon: PV get: %s - %d" % (pv.pvname, pv.value))

            if pv.value != None:		# just to be sure...
               metric = collectd.Values()
               metric.plugin = doc[pv.pvname]['sector']
               metric.type = doc[pv.pvname]['measure']
               metric.plugin_instance = str(doc[pv.pvname]['id'])
               metric.values = [round(pv.value,doc[pv.pvname]['round'])]
               metric.meta = {'0': True}
               metric.dispatch()

   # uSOP board voltages

   f = open("/sys/bus/iio/devices/iio:device0/in_voltage7_raw",'r')
   value_raw = int(f.read());
   value_sys_V = 2 * (1.8 * value_raw) / 4095
   f.close()

   if value_sys_V != None:
      metric = collectd.Values()
      metric.plugin = "board"
      metric.type = "voltage"
      metric.plugin_instance = "1";
      metric.values = [round(value_sys_V, 2)]
      metric.meta = {'0': True}
      metric.dispatch()

   f = open("/sys/bus/iio/devices/iio:device0/in_voltage1_raw",'r')
   value_raw = int(f.read());
   value_bus_V = 2 * (1.8 * value_raw) / 4095
   f.close()      

   if value_bus_V != None:
      metric = collectd.Values()
      metric.plugin = "bus"
      metric.type = "voltage"
      metric.plugin_instance = "1";
      metric.values = [round(value_bus_V, 2)]
      metric.meta = {'0': True}
      metric.dispatch()

collectd.register_init(init_callback)
collectd.register_read(read_callback)
