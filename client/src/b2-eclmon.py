#!/usr/bin/env python

import collectd
import signal
import epics
import yaml

"""
example of metric name:
    collectd.usop.S1B.1.humidity
"""

debug = False

doc = {}
pvs = set()
pvstate = {}

def onConnectionChange(pvname=None, conn=None, **kws):
   collectd.info('b2-eclmon: PV connection status changed: %s %s' % (pvname,  repr(conn)))
   pvstate[pvname] = conn

def init_callback():
 
   global debug
   global doc, pvs, pvstate

   stream = file('/opt/collectd-plugins/b2-ecl-sec.yaml', 'r')

   try:
      doc = yaml.load(stream)
   except yaml.YAMLError, exc:
      collectd.info("b2-eclmon: error in configuration file: %s" % (exc))

   if debug:
      collectd.info("init - dump config file: %s" % (yaml.dump(doc)))

   for pv in doc:
      pvs.add(epics.PV(pv, connection_callback=onConnectionChange))

   for pv in pvs:
      pvstate[pv.pvname] = False

   collectd.info("b2-eclmon: plugin started")

   stream.close()

def read_callback(data=None):

   global debug
   global doc, pvs, pvstate
   
   for pv in pvs:

      if pv.pvname in pvstate:
         if pvstate[pv.pvname] == True:		# PV is connected

            pv.get()

            if debug:
               collectd.info("b2-eclmon: PV get: %s - %d" % (pv.pvname, pv.value))

            if pv.value <> None:		# just to be sure...
               metric = collectd.Values()
               metric.plugin = doc[pv.pvname]['sector']
               metric.type = doc[pv.pvname]['measure']
               metric.plugin_instance = str(doc[pv.pvname]['id'])
               metric.values = [pv.value]
               metric.meta = {'0': True}
               metric.dispatch()

collectd.register_init(init_callback)
collectd.register_read(read_callback)
