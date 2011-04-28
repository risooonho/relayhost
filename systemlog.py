# -*- coding: utf-8 -*-
from tasbot.ParseConfig import *
import time
import datetime
import os
import sys
from tasbot.customlog import Log
from tasbot.Plugin import IPlugin

class Main(IPlugin):
	def __init__(self,name,tasclient):
		IPlugin.__init__(self,name,tasclient)
		
	def onload(self,tasc):
		pass
	
	def oncommandfromserver(self,command,args,socket):
		if command == "SAID" and args[0] == "autohost":
		  Log.Debug("<%s> %s" % ( args[1] , " ".join(args[2:])))
		if command == "SAIDEX" and args[0] == "autohost":
		  Log.Debug("* %s %s" % ( args[1] , " ".join(args[2:])))
		if command == "JOINED" and args[0] == "autohost":
		  Log.Info("** %s has joined the channel\n" % (args[1]))
		if command == "LEFT" and args[0] == "autohost":
		  Log.Info("** %s has left the channel ( %s )\n" % ( args[1] , " ".join(args[2:])))
		  
	def onloggedin(self,socket):
		Log.Info("********** CONNECTED ***********\n")
