#!/bin/env python

import sys, re
import time, datetime, os

sys.path.append('/home/mdalchen/gemdev/gem-daq-code/gemdaq-testing/setup/scripts/src')
#sys.path.append('/opt/gemdaq/firmware/testing/src')

import uhal
from registers_uhal import *
from glib_system_info_uhal import *
from rate_calculator import errorRate
from glib_user_functions_uhal import *

#from glib_clock_src import *

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-s", "--slot", type="int", dest="slot",
		  help="slot in uTCA crate", metavar="slot", default=15)
parser.add_option("-g", "--gtx", type="int", dest="gtx",
		  help="GTX on the GLIB", metavar="gtx", default=0)
parser.add_option("-c", "--clksrc", type="string", dest="clksrc",
		  help="select the input for the XPoint1 outputs", metavar="clksrc", default="local")
parser.add_option("-r", "--reset", action="store_true", dest="resetCounters",
		  help="reset link error counters", metavar="resetCounters")
parser.add_option("-x", "--external", type="int", dest="trgSrc",
		  help="change trigger source", metavar="trgSrc")
parser.add_option("-b", "--sbitout", type="int", dest="sbitSrc",
		  help="use s-bit from VFAT <num>", metavar="sbitSrc")
parser.add_option("-d", "--debug", action="store_true", dest="debug",
		  help="print extra debugging information", metavar="debug")
parser.add_option("-e", "--errors", type="int", dest="errorRate", default=1,
		  help="calculate link error rates for N seconds", metavar="errorRate")
parser.add_option("-u", "--user", action="store_true", dest="userOnly",
		  help="print user information only", metavar="userOnly")
parser.add_option("--testbeam", action="store_true", dest="testbeam",
		  help="fixed IP address for testbeam", metavar="testbeam")
parser.add_option("--daq_enable", type="int", dest="daq_enable",
		  help="enable daq output", metavar="daq_enable", default=-1)
(options, args) = parser.parse_args()

uhal.setLogLevelTo( uhal.LogLevel.FATAL )

uTCAslot = 175
if options.slot:
	uTCAslot = 160+options.slot
print options.slot, uTCAslot
ipaddr = '192.168.0.%d'%(uTCAslot)
if options.testbeam:
        ipaddr        = '137.138.115.185'
address_table = "file://${GEM_ADDRESS_TABLE_PATH}/glib_address_table.xml"
uri = "chtcp-2.0://localhost:10203?target=%s:50001"%(ipaddr)
glib  = uhal.getDevice( "glib" , uri, address_table )

########################################
# IP address
########################################
print
print "--=======================================--"
print "  Opening GLIB with IP", ipaddr
print "--=======================================--"
print

if not options.userOnly:
	getSystemInfo(glib)
	
print
print "--=======================================--"
print "-> DAQ INFORMATION"
print "--=======================================--"
print

print "-> GLIB L1A ID :0x%08x"%(readRegister(glib,"GLIB.DAQ.L1AID"))

if (options.daq_enable>=0):
  writeRegister(glib, "GLIB.DAQ.CONTROL", options.daq_enable)
  print "Reset daq_enable: %i"%(options.daq_enable)

print "-> GLIB DAQ control reg :0x%08x"%(readRegister(glib,"GLIB.DAQ.CONTROL"))
print "-> GLIB DAQ status reg :0x%08x"%(readRegister(glib,"GLIB.DAQ.STATUS"))
print "-> GLIB DAQ global flags :0x%08x"%(readRegister(glib,"GLIB.DAQ.FLAGS"))
print "-> GLIB DAQ corrupted VFAT block counter :0x%08x"%(readRegister(glib,"GLIB.DAQ.CORRUPT_CNT"))
print "-> GLIB DAQ built events cnt :0x%08x"%(readRegister(glib,"GLIB.DAQ.EVT_BUILT"))
print "-> GLIB DAQ sent events cnt :0x%08x"%(readRegister(glib,"GLIB.DAQ.EVT_SENT"))

print "-> GLIB DAQ GTX dispersion error counter :0x%08x"%(readRegister(glib,"GLIB.DAQ.DISPER_ERR"))
print "-> GLIB DAQ GTX NOT_IN_TABLE error counter :0x%08x"%(readRegister(glib,"GLIB.DAQ.NOTINTABLE_ERR"))

print "-> GLIB DAQ debug0 :0x%08x"%(readRegister(glib,"GLIB.DAQ.DEBUG_0"))
print "-> GLIB DAQ debug1 :0x%08x"%(readRegister(glib,"GLIB.DAQ.DEBUG_1"))
print "-> GLIB DAQ debug2 :0x%08x"%(readRegister(glib,"GLIB.DAQ.DEBUG_2"))
print "-> GLIB DAQ debug3 :0x%08x"%(readRegister(glib,"GLIB.DAQ.DEBUG_3"))
print "-> GLIB DAQ debug4 :0x%08x"%(readRegister(glib,"GLIB.DAQ.DEBUG_4"))
print "-> GLIB DAQ debug5 :0x%08x"%(readRegister(glib,"GLIB.DAQ.DEBUG_5"))
print "-> GLIB DAQ debug6 :0x%08x"%(readRegister(glib,"GLIB.DAQ.DEBUG_6"))

print
print "--=======================================--"
print "-> BOARD USER INFORMATION"
print "--=======================================--"
print

if (options.resetCounters):
        glibCounters(glib,options.gtx,True)
print
sys.stdout.flush()
errorCounts = []
SAMPLE_TIME = 1.
for trial in range(options.errorRate):
        errorCounts.append(calculateLinkErrors(True,glib,options.gtx,SAMPLE_TIME))
sys.stdout.flush()

rates = errorRate(errorCounts,SAMPLE_TIME)
#counters = optohybridCounters(optohybrid)
print "-> TRK: 0x%08x  (%6.2f%1sHz)"%(rates["TRK"][0],rates["TRK"][1],rates["TRK"][2])
print "-> TRG: 0x%08x  (%6.2f%1sHz)"%(rates["TRG"][0],rates["TRG"][1],rates["TRG"][2])
print 

sys.stdout.flush()
print "-> Counters    %8s     %8s     %8s     %8s"%("L1A","Cal","Resync","BC0")
counters = glibCounters(glib,options.gtx)
print "   %8s  0x%08x   0x%08x   0x%08x   0x%08x"%(
        "",
        counters["T1"]["L1A"],
        counters["T1"]["CalPulse"],
        counters["T1"]["Resync"],
        counters["T1"]["BC0"])
print "--=======================================--"
sys.stdout.flush()
