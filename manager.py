# -*- coding: utf-8 -*-
#from tasbot.ParseConfig import *
import tasbot
import commands
from tasbot.customlog import Log
import thread
import os
import sys
import signal
import traceback
import subprocess
import platform
import time
if platform.system() == "Windows":
  import win32api

def parseportrange(arg):
	separator = ":"
	tempvariable = []
	if ( arg.find( separator ) >= 0 ):
		extremes = parselist(arg,separator)
		for num in range( int(extremes[0]), int(extremes[1]) +1 ):
			tempvariable.append(str(num))
	else:
		tempvariable.append(arg)
	return tempvariable
class Main:
	ul = []
	listfull = False
	bots = dict()
	disabled = False
	botstatus = dict()
	def botthread(self,slot,nick,s,r,p,ist):
		try:
			self.say_ah("Spawning (Requested by %s) " % r +nick)
			d = dict()
			d.update([("serveraddr",self.app.config["serveraddr"])])
			d.update([("spawnedby",r)])
			d.update([("serverport",self.app.config["serverport"])])
			d.update([("springdedpath",self.app.config["springdedpath"])])
			if "springdatapath" in self.app.config:
				d.update([("springdatapath",self.app.config["springdatapath"])])
			if "bindip" in self.app.config:
				d.update([("bindip",self.app.config["bindip"])])
			d.update([("admins",self.app.config["admins"])])
			d.update([("nick",nick)])
			d.update([("password",p)])
			d.update([("hostport",self.hostports[slot])])
			d.update([("ahport",self.controlports[slot])])
			d.update([("plugins","channels,autohost,help")])
			d.update([("bans",self.app.config["bans"])])
			d.update([("keepscript",self.app.config["keepscript"])])
			tasbot.ParseConfig.writeconfigfile(nick+".cfg",d)
			#p = subprocess.Popen(("python","Main.py","-c", "%s" % (nick+".cfg")),stdout=sys.stdout)
			cfg = "%s" % (nick+".cfg")
			inst = tasbot.DefaultApp( cfg, cfg+".pid", False, True)
			inst.run()
			#self.bots.update([(nick,p.pid)])
			#print self.bots
			#p.wait()
			self.say_ah("Destroying "+nick)
			if r in self.ul:
			    self.ul.remove(r)

			if ist.listfull:
				ist.listfull = False
				ist.updatestatus(s)
			ist.botstatus[slot] = False
		except Exception,e:
			Log.Except( e )
	def onload(self,tasc):
		self.tasclient = tasc
		self.bans = []
		self.app = tasc.main
		self.bans = parselist(self.app.config["bans"],",")
		self.hostports = []
		for port in parselist(self.app.config["hostports"],","):
			self.hostports = self.hostports + parseportrange( port )
		self.controlports = []
		for port in parselist(self.app.config["ahports"],","):
			self.controlports = self.controlports + parseportrange( port )
		numhosts = min( len(self.hostports), len(self.controlports) ) # number of host is minimum between amount of free ports for host and amount of free ports for control
		self.an = []
		basenick = self.app.config["slavesnick"]
		for i in range( 1, numhosts + 1 ): # fill the list of host names with the format of basenick + slot number
			self.an.append( basenick + str(i) )
		self.ap = self.app.config["slavespass"]
		self.disabled = not bool(int(self.app.config["enabled"]))
		for i in range( 0, numhosts ):
			self.botstatus.update([(i,False)])
	def oncommandfromserver(self,command,args,socket):
		try:
			if command == "SAIDPRIVATE" and len(args) == 2 and args[1] == "!enable" and args[0] in self.app.admins:
				self.disabled = False
				socket.send("MYSTATUS %i\n" % int(int(self.listfull)+int(self.disabled)*2))
				socket.send("SAYPRIVATE %s %s\n" % (args[0],"Hosting new games enabled"))
				self.app.config["enabled"] = "1"
				self.app.SaveConfig()
			elif command == "SAIDPRIVATE" and len(args) == 2 and args[1] == "!disable" and args[0] in self.app.admins:
				self.disabled = True
				socket.send("MYSTATUS %i\n" % int(int(self.listfull)+int(self.disabled)*2))
				socket.send("SAYPRIVATE %s %s\n" % (args[0],"Hosting new games disabled"))
				self.app.config["enabled"] = "0"
				self.app.SaveConfig()
			elif command == "SAIDPRIVATE" and len(args) == 2 and args[1] == "!listbans" and args[0] in self.app.admins:
				x = 0
				l0 = []
				for b in self.bans:
					l0.append(b)
					x += 1
					if x >= 5:
						socket.send("SAYPRIVATE %s %s\n" % (args[0],' | '.join(l0)))
						x = 0
						l0 = []
				socket.send("SAYPRIVATE %s %s\n" % (args[0],' | '.join(l0)))
			elif command == "SAIDPRIVATE" and len(args) >= 3 and args[1] == "!ban" and args[0] in self.app.admins:
				toban = args[2:]
				for b in toban:
					if not b in self.bans:
						self.bans.append(b)
						socket.send("SAYPRIVATE %s %s\n" % (args[0],b+" Banned"))
					else:
						socket.send("SAYPRIVATE %s %s\n" % (args[0],b+" is already banned"))
				self.app.config["bans"] = ','.join(self.bans)
				self.app.SaveConfig()
				socket.send("SAYPRIVATE %s %s\n" % (args[0],"Done."))
			elif command == "SAIDPRIVATE" and len(args) >= 3 and args[1] == "!unban" and args[0] in self.app.admins:
				toban = args[2:]
				for b in toban:
					if not b in self.bans:
						socket.send("SAYPRIVATE %s %s\n" % (args[0],b+"is not currently banned"))
					else:
						self.bans.remove(b)
						socket.send("SAYPRIVATE %s %s\n" % (args[0],b+" has been unbanned"))
				self.app.config["bans"] = ','.join(self.bans)
				self.app.SaveConfig()
				socket.send("SAYPRIVATE %s %s\n" % (args[0],"Done."))
			elif command == "SAIDPRIVATE" and len(args) == 2 and args[1] == "!registerall" and args[0] in self.app.admins:
				for b in self.botstatus:
					if not self.botstatus[b]:
						slot = b
						self.threads.append(thread.start_new_thread(self.botthread,(slot,self.an[slot],socket,args[0],self.ap,self)))
						self.botstatus[slot] = True
						time.sleep(1)
						if b + 1 == len(self.botstatus): # The bot spawned was the last one
							self.listfull = True
							socket.send("MYSTATUS 1\n")
			elif command == "SAIDPRIVATE" and len(args) == 2 and args[1] == "!spawn" and args[0] not in self.ul and not self.disabled:
				if args[0] in self.bans:
					socket.send("SAYPRIVATE %s %s\n" %(args[0],"\001 Error: You are banned!"))
					return
				freeslot = False
				slot = 0
				for b in self.botstatus:
					if not self.botstatus[b]:
						freeslot = True
						slot = b
						break
				if freeslot:
					self.threads.append(thread.start_new_thread(self.botthread,(slot,self.an[slot],socket,args[0],self.ap,self)))
					socket.send("SAYPRIVATE %s %s\n" %(args[0],self.an[slot]))
					self.ul.append(args[0])
					self.botstatus[slot] = True
					if b + 1 == len(self.botstatus): # The bot spawned was the last one
						self.listfull = True
						socket.send("MYSTATUS 1\n")
				else:
					socket.send("SAYPRIVATE %s %s\n" %(args[0],"\001 Error: All bots are spawned"))

			#elif command == "SAIDPRIVATE" and len(args) == 2 and args[1] == "!spawn" and len(self.ul) >= len(self.an):
			#	socket.send("SAYPRIVATE %s %s\n" %(args[0],"\001 Error: All bots are spawned"))
			#elif command == "SAIDPRIVATE" and len(args) >= 1 and :
			#	socket.send("SAYPRIVATE %s %s\n" %(args[0],"\002"))
			elif command == "LEFT" and args[0] == "autohost" and len(args) > 4 and args[3] == "inconsistent" and args[1] in self.bots:
				self.say_ah("Bot(%s) kicked by inconsistent data error , killing" % args[1])
				try:
					if platform.system() == "Windows":
					  handle = win32api.OpenProcess(1, 0, self.bots[args[1]])
					  win32api.TerminateProcess(handle, 0)
					else:
					  os.kill(self.bots[args[1]],signal.SIGKILL)
				except:
					pass
		except:
			exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
			self.sayex_ah("*** EXCEPTION: BEGIN")
			for line in exc:
				self.sayex_ah(line)
			self.sayex_ah("*** EXCEPTION: END")

	def updatestatus(self,socket):
		socket.send("MYSTATUS %i\n" % int(int(self.listfull)+int(self.disabled)*2))

	def onloggedin(self,socket):
		self.updatestatus(socket)
		
	def say_ah(self,message):
		try:
			self.tasclient.say("autohost", message)
		except:
			pass

	def sayex_ah(self,message):
		try:
			self.tasclient.sayex("autohost", message)
		except:
			pass		

