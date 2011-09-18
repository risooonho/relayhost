# -*- coding: utf-8 -*-
import commands
import thread
import signal
import os
import time
import subprocess
import platform
import sys
import traceback
if platform.system() == "Windows":
	import win32api

from tasbot.utilities import *
from tasbot.plugin import IPlugin

import udpinterface

class Main(IPlugin):
	def __init__(self,name,tasclient):
		IPlugin.__init__(self,name,tasclient)
		self.sock = self.tasclient.socket
		self.app = None
		self.hosted = 0
		self.battleowner = ""
		self.battleid = 0
		self.status = 0
		self.pr = 0
		self.noowner = True
		self.script = ""
		self.used = 0
		self.hosttime = 0.0
		self.redirectjoins = False
		self.gamestarted = False
		if platform.system() == "Windows":
			self.scriptbasepath = os.environ['USERPROFILE']
		else:
			self.scriptbasepath = os.environ['HOME']
		self.redirectspring = False
		self.redirectbattleroom = False
		self.users = dict()
		self.logger.debug( "INIT MoTH" )

	def ecb(self,event,data):
		if self.redirectspring:
			ags = []
			data2 = ""
			for c in data:
				if ord(c) < 17:
					ags.append(ord(c))
				else:
					data2 += c
			self.saypm(self.battleowner,"#"+str(event)+"#".join(ags)+" "+data2)

	def onloggedin(self,socket):
		self.hosted = 0
		self.sock = socket

	def mscb(self,p,msg):
		try:
			if p == self.battleowner:
				if msg.startswith("!"):
					self.u.sayingame("/"+msg[1:])
		except Exception, e:
			self.logger.exception(e)
			exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
			self.sayex("*** EXCEPTION: BEGIN")
			for line in exc:
				self.sayex(line)
			self.sayex("*** EXCEPTION: END")

	def killbot(self):
		self.logger.info( "setting force_quit True" )
		self.app.dying = True

	def timeoutthread(self):
		while 1:
			time.sleep(20.0)
			try:
				if not ( not self.noowner and self.hosted == 1) and not self.gamestarted:
					self.logger.error("Timeouted hosting")
					self.killbot()
					return
			except Exception,e:
				self.logger.debug('hosting timeout')
				self.logger.exception(e)

	def startspring(self,socket,g):
		currentworkingdir = os.getcwd()
		try:
			self.u.reset()
			if self.gamestarted:
				socket.send("SAYBATTLEEX *** Error: game is already running\n")
				return
			self.output = ""
			socket.send("SAYBATTLEEX *** Starting game...\n")
			socket.send("MYSTATUS 1\n")
			st = time.time()
			#status,j = commands.getstatusoutput("spring-dedicated "+os.path.join(self.scriptbasepath,"%f.txt" % g ))
			self.sayex("*** Starting spring: command line \"%s\"" % (self.app.config.get('tasbot', "springdedpath")+" "+os.path.join(self.scriptbasepath,"%f.txt" % g )))
			if platform.system() == "Windows":
				dedpath = "\\".join(self.app.config.get('tasbot', "springdedpath").replace("/","\\").split("\\")[:self.app.config.get('tasbot', "springdedpath").replace("/","\\").count("\\")])
				if not dedpath in sys.path:
					sys.path.append(dedpath)
			if self.app.config.has_option('tasbot', "springdatapath"):
				springdatapath = self.app.config.get('tasbot', "springdatapath")
				if not springdatapath in sys.path:
					sys.path.append(springdatapath)
				os.chdir(springdatapath)
			else:
				springdatapath = None
			if springdatapath!= None:
				os.environ['SPRING_DATADIR'] = springdatapath
			self.pr = subprocess.Popen((self.app.config.get('tasbot', "springdedpath"),os.path.join(self.scriptbasepath,"%f.txt" % g )),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=springdatapath)
			self.gamestarted = True
			l = self.pr.stdout.readline()
			while len(l) > 0:
				self.output += l
				l = self.pr.stdout.readline()
			status = self.pr.wait()
			self.sayex("*** Spring has exited with status %i" % status )
			et = time.time()


			if status != 0:
				socket.send("SAYBATTLEEX *** Error: Spring Exited with status %i\n" % status)
				g = self.output.split("\n")
				for h in g:
					self.sayex("*** STDOUT+STDERR: "+h)
					time.sleep(float(len(h))/900.0+0.05)
			socket.send("MYSTATUS 0\n")
			socket.send("SAYBATTLEEX *** Game ended\n")
		except Exception,e:
			exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
			self.sayex("*** EXCEPTION: BEGIN")
			for line in exc:
				self.sayex(line)
			self.sayex("*** EXCEPTION: END")
		try:
			if int(self.app.config.get('autohost', "keepscript")) == 0:
				os.remove(os.path.join(self.scriptbasepath,"%f.txt" % g))
		except Exception,e:
			self.logger.debug('failed to remove script')
		os.chdir(currentworkingdir)
		self.gamestarted = False
		if self.noowner == True:
			self.sayex("The host is no longer in the battle, exiting")
			self.logger.info("Exiting")
			self.killbot()

	def onload(self,tasc):
		try:
			self.tasclient = tasc
			self.app = tasc.main
			self.hosttime = time.time()
			self.start_thread(self.timeoutthread)
			self.u = udpinterface.UDPint(int(self.app.config.get('autohost', "ahport")),self.mscb,self.ecb)
		except Exception, e:
			self.logger.exception(e)

	def oncommandfromserver(self,command,args,s):
		#print "From server: %s | Args : %s" % (command,str(args))
		self.sock = s
		if command == "RING" and len(args) > 0:
			s.send("RING " + self.app.config.get('autohost', "spawnedby") + "\n")
		if command == "CLIENTBATTLESTATUS" and len(args) > 0 and self.redirectbattleroom:
			self.saypm(self.app.config.get('autohost', "spawnedby"), "!" + command + " " + " ".join(args[0:]) )
		if command == "SAIDBATTLE" and len(args) > 0:
			if self.redirectbattleroom:
				self.saypm(self.app.config.get('autohost', "spawnedby"), "!" + command + " " + " ".join(args[0:]))
			if args[1].startswith("!") and args[0] == self.battleowner:
				try:
					msg = " ".join(args[1:])
					self.u.sayingame("/"+msg[1:])
				except Exception,e:
					exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
					self.sayex("*** EXCEPTION: BEGIN")
					for line in exc:
						self.sayex(line)
		if command == "SAIDBATTLEEX" and len(args) > 0 and self.redirectbattleroom:
			self.saypm(self.app.config.get('autohost', "spawnedby"), "!" + command + " " + " ".join(args[0:]))
		if command == "REQUESTBATTLESTATUS":
			s.send( "MYBATTLESTATUS 4194816 255\n" )#spectator+synced/white
		if command == "SAIDPRIVATE" and args[0] not in self.app.config.get('autohost', "bans") and args[0] == self.app.config.get('autohost', "spawnedby"):
			if args[1] == "!openbattle" and not self.hosted == 1:
				if len(args) < 6:
					self.logger.error("Got invalid openbattle with params:"+" ".join(args))
					return
				args[5] = self.app.config.get('autohost',"hostport")
				self.logger.info("OPENBATTLE "+" ".join(args[2:]))
				s.send("OPENBATTLE "+" ".join(args[2:])+"\n")
				self.battleowner = args[0]
				return
			elif args[1] == "!openbattle" and self.hosted == 1:
				self.saypm(args[0],"E1 | Battle is already hosted")
				return
			elif args[1] == "!supportscriptpassword":
				self.redirectjoins = True
				return
			elif self.hosted == 1 and args[0] == self.battleowner:
				if args[1] == "!setingamepassword":
					try:
						msg = " ".join(args[2:])
						self.u.sayingame("/adduser "+msg)
					except Exception,e:
						exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
						self.sayex("*** EXCEPTION: BEGIN")
						for line in exc:
							self.sayex(line)
				if args[1] == "!addstartrect":
					s.send("ADDSTARTRECT "+" ".join(args[2:])+"\n")
				if args[1] == "!setscripttags":
					s.send("SETSCRIPTTAGS "+" ".join(args[2:])+"\n")
				if args[1] == "!removestartrect":
					s.send("REMOVESTARTRECT "+" ".join(args[2:])+"\n")
				if args[1] == "!leavebattle":
					s.send("LEAVEBATTLE\n")
					self.hosted = 0
				if args[1] == "!updatebattleinfo":
					s.send("UPDATEBATTLEINFO "+" ".join(args[2:])+"\n")
				if args[1] == "!kickfrombattle":
					s.send("KICKFROMBATTLE "+" ".join(args[2:])+"\n")
				if args[1] == "!addbot":
					s.send("ADDBOT "+" ".join(args[2:])+"\n")
				if args[1] == "!handicap":
					s.send("HANDICAP "+" ".join(args[2:])+"\n")
				if args[1] == "!forceteamcolor":
					s.send("FORCETEAMCOLOR "+" ".join(args[2:])+"\n")
				if args[1] == "!forceallyno":
					s.send("FORCEALLYNO "+" ".join(args[2:])+"\n")
				if args[1] == "!forceteamno":
					s.send("FORCETEAMNO "+" ".join(args[2:])+"\n")
				if args[1] == "!disableunits":
					s.send("DISABLEUNITS "+" ".join(args[2:])+"\n")
				if args[1] == "!enableallunits":
					s.send("ENABLEALLUNITS "+" ".join(args[2:])+"\n")
				if args[1] == "!removebot":
					s.send("REMOVEBOT "+" ".join(args[2:])+"\n")
				if args[1] == "!updatebot":
					s.send("UPDATEBOT "+" ".join(args[2:])+"\n")
				if args[1] == "!ring":
					s.send("RING "+" ".join(args[2:])+"\n")
				if args[1] == "!forcespectatormode":
					s.send("FORCESPECTATORMODE "+" ".join(args[2:])+"\n")
				if args[1] == "!redirectspring" and len(args) > 1:
					try:
						if ( self.tasclient.users[self.battleowner].bot ):
							self.redirectspring = bool(args[2])
					except Exception,e:
						exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
						self.sayex("*** EXCEPTION: BEGIN")
						for line in exc:
							self.sayex(line)
						self.sayex("*** EXCEPTION: END")
				if args[1] == "!redirectbattleroom"and len(args) > 1:
					try:
						if ( self.tasclient.users[self.battleowner].bot ):
							self.redirectbattleroom = bool(args[2])
					except Exception,e:
						exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
						self.sayex("*** EXCEPTION: BEGIN")
						for line in exc:
							self.sayex(line)
						self.sayex("*** EXCEPTION: END")
				if args[1] == "!cleanscript":
					self.script = ""
				if args[1] == "!appendscriptline":
					self.script += " ".join(args[2:])+"\n"
				if args[1].startswith("#") and args[0] == self.battleowner:
					try:
						msg = " ".join(args[1:])
						self.u.sayingame(msg[1:])
					except Exception,e:
						exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
						self.sayex("*** EXCEPTION: BEGIN")
						for line in exc:
							self.sayex(line)
				if args[1] == "!saybattle":
					s.send("SAYBATTLE "+" ".join(args[2:])+"\n")
				if args[1] == "!saybattleex":
					s.send("SAYBATTLEEX "+" ".join(args[2:])+"\n")
				if args[1] == "!startgame":
					if not self.gamestarted:
						s.send("MYSTATUS 1\n")
						g = time.time()
						try:
							os.remove(os.path.join(self.scriptbasepath,"%f.txt" % g))
						except Exception,e:
							pass
						f = open(os.path.join(self.scriptbasepath,"%f.txt" % g),"a")
						s1 = self.script.find("MyPlayerName=")
						s2 = self.script[s1:].find(";")+1+s1
						self.script = self.script.replace(self.script[s1:s2],"MyPlayerName=%s;\n\tAutoHostPort=%i;" % 
							(self.app.config.get('tasbot', "nick"),int(self.app.config.get('autohost', "ahport"))))
						s1 = self.script.find("HostIP=")
						s2 = self.script[s1:].find(";")+1+s1
						if self.app.config.has_option('autohost', "bindip"):
							self.script = self.script.replace(self.script[s1:s2],"HostIP=%s;" % (self.app.config.get('autohost', "bindip")))
						else:
							self.script = self.script[0:s1] + self.script[s2:]
						f.write(self.script)
						f.close()
						thread.start_new_thread(self.startspring,(s,g))
					else:
						self.saypm(args[0],"E3 | Battle already started")
			else:
				self.saypm(args[0],"E2 | Battle is not hosted")

		if command == "OPENBATTLE":
			self.battleid = int(args[0])
			self.used = 1
			self.sayex("Battle hosted succesfully , id is %s" % args[0])
		if command == "JOINEDBATTLE" and len(args) >= 2 and int(args[0]) == self.battleid:
			if args[1] == self.battleowner:
				self.hosted = 1
				self.noowner = False
				self.sayex("The host has joined the battle")
				s.send("SAYBATTLE Hello, the bot accepts all commands from normal spring prefixed with ! instead of /\n")
				s.send("SAYBATTLE read Documentation/cmds.txt for a list of spring commands\n")
				s.send("SAYBATTLE in order to stop a game immediately, use !kill\n")
			if self.redirectjoins:
				self.saypm(self.battleowner,command + " " + " ".join(args[0:])) # redirect the join command to the owner so he can manage script password
		if command == "SERVERMSG":
			self.saypm(self.battleowner," ".join(args))
		if command == "LEFTBATTLE" and int(args[0]) == self.battleid and args[1] == self.battleowner:
			if	not self.gamestarted:
				self.sayex("The host has left the battle and the game isn't running, exiting")
				s.send("LEAVEBATTLE\n")
				try:
					if platform.system() == "Windows":
						handle = win32api.OpenProcess(1, 0, self.pr.pid)
						win32api.TerminateProcess(handle, 0)
					else:
						os.kill(self.pr.pid,signal.SIGKILL)
				except Exception,e:
					pass
				self.killbot()

			self.noowner = True

		if command == "REMOVEUSER" and args[0] == self.battleowner:
			if	not self.gamestarted:
				self.sayex("The host disconnected and game not started, exiting")
				try:
					if platform.system() == "Windows":
						handle = win32api.OpenProcess(1, 0, self.pr.pid)
						win32api.TerminateProcess(handle, 0)
					else:
						os.kill(self.pr.pid,signal.SIGKILL)
				except Exception,e:
					pass
				self.killbot()
			self.noowner = True

	def onloggedin(self,socket):
		self.noowner = True
		self.hosted = 0
		if self.gamestarted:
			socket.send("MYSTATUS 1\n")

	def saypm(self,p,m):
		try:
			self.logger.debug("PM To:%s, Message: %s" %(p,m))
			self.tasclient.socket.send("SAYPRIVATE %s %s\n" %(p,m))
		except Exception, e:
			self.logger.exception(e)

	def say(self,m):
		try:
			self.logger.debug("SAY autohost %s\n" % m)
			self.tasclient.socket.send("SAY autohost %s\n" % m)
		except Exception, e:
			self.logger.exception(e)

	def sayex(self,m):
		try:
			self.logger.debug("SAYEX autohost %s\n" % m)
			self.tasclient.socket.send("SAYEX autohost %s\n" % m)
		except Exception, e:
			self.logger.exception(e)
