# -*- coding: utf-8 -*-
from tasbot.ParseConfig import *
import commands
import thread
import signal
import os
import time
import udpinterface
import subprocess
import traceback
import platform
import sys
from tasbot.customlog import Log
if platform.system() == "Windows":
	import win32api
from tasbot.utilities import *
def pm(s,p,m):
	try:
		Log.Debug("PM To:%s, Message: %s" %(p,m))
		s.send("SAYPRIVATE %s %s\n" %(p,m))
	except:
		pass
def logc(s,m):
	try:
		Log.Debug("SAY autohost %s\n" % m)
		s.send("SAY autohost %s\n" % m)
	except:
		pass
def loge(s,m):
	try:
		Log.Debug("SAYEX autohost %s\n" % m)
		s.send("SAYEX autohost %s\n" % m)
	except:
		pass
class Main:
	sock = 0
	hosted = 0
	battleowner = ""
	battleid = 0
	status = 0
	pr = 0
	noowner = True
	script = ""
	used = 0
	app = 0
	hosttime = 0.0
	redirectjoins = False
	gamestarted = False
	if platform.system() == "Windows":
		scriptbasepath = os.environ['USERPROFILE']
	else:
		scriptbasepath = os.environ['HOME']
	redirectspring = False
	redirectbattleroom = False
	users = dict()
	def ecb(self,event,data):
		if self.redirectspring:
			ags = []
			data2 = ""
			for c in data:
				if ord(c) < 17:
					ags.append(ord(c))
				else:
					data2 += c
			pm(self.sock,self.battleowner,"#"+str(event)+"#".join(ags)+" "+data2)
	def onloggedin(self,socket):
		self.hosted = 0
		self.sock = socket
	def mscb(self,p,msg):
		try:
			if p == self.battleowner:
				if msg.startswith("!"):
					self.u.sayingame("/"+msg[1:])
		except:
			exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
			loge(socket,"*** EXCEPTION: BEGIN")
			for line in exc:
				loge(self.sock,line)
			loge(socket,"*** EXCEPTION: END")

	def killbot(self):
		if platform.system() == "Windows":
			handle = win32api.OpenProcess(1, 0, os.getpid())
			win32api.TerminateProcess(handle, 0)
		else:
			os.kill(os.getpid(),signal.SIGKILL)

	def timeoutthread(self):
		while 1:
			time.sleep(20.0)
			try:
				if not ( not self.noowner and self.hosted == 1) and not self.gamestarted:
					Log.Error("Timeouted hosting")
					self.killbot()
			except:
				pass

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
			loge(socket,"*** Starting spring: command line \"%s\"" % (self.app.config["springdedpath"]+" "+os.path.join(self.scriptbasepath,"%f.txt" % g )))
			if platform.system() == "Windows":
				dedpath = "\\".join(self.app.config["springdedpath"].replace("/","\\").split("\\")[:self.app.config["springdedpath"].replace("/","\\").count("\\")])
				if not dedpath in sys.path:
					sys.path.append(dedpath)
			if "springdatapath" in self.app.config:
				springdatapath = self.app.config["springdatapath"]
				if not springdatapath in sys.path:
					sys.path.append(springdatapath)
				os.chdir(springdatapath)
			else:
				springdatapath = None
			if springdatapath!= None:
				os.environ['SPRING_DATADIR'] = springdatapath
			self.pr = subprocess.Popen((self.app.config["springdedpath"],os.path.join(self.scriptbasepath,"%f.txt" % g )),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=springdatapath)
			self.gamestarted = True
			l = self.pr.stdout.readline()
			while len(l) > 0:
				self.output += l
				l = self.pr.stdout.readline()
			status = self.pr.wait()
			loge(socket,"*** Spring has exited with status %i" % status )
			et = time.time()


			if status != 0:
				socket.send("SAYBATTLEEX *** Error: Spring Exited with status %i\n" % status)
				g = self.output.split("\n")
				for h in g:
					loge(socket,"*** STDOUT+STDERR: "+h)
					time.sleep(float(len(h))/900.0+0.05)
			socket.send("MYSTATUS 0\n")
			socket.send("SAYBATTLEEX *** Game ended\n")
		except:
			exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
			loge(socket,"*** EXCEPTION: BEGIN")
			for line in exc:
				loge(socket,line)
			loge(socket,"*** EXCEPTION: END")
		try:
			if int(self.app.config["keepscript"]) == 0:
				os.remove(os.path.join(self.scriptbasepath,"%f.txt" % g))
		except:
			pass
		os.chdir(currentworkingdir)
		self.gamestarted = False
		if self.noowner == True:
			loge(socket,"The host is no longer in the battle, exiting")
			Log.Info("Exiting")
			self.killbot()
	def onload(self,tasc):
		try:
			self.tsc = tasc
			self.app = tasc.main
			self.hosttime = time.time()
			thread.start_new_thread(self.timeoutthread,())
			self.u = udpinterface.UDPint(int(self.app.config["ahport"]),self.mscb,self.ecb)
		except Exception, e:
			Log.Except( e )

	def oncommandfromserver(self,command,args,s):
		#print "From server: %s | Args : %s" % (command,str(args))
		self.sock = s
		if command == "RING" and len(args) > 0:
			s.send("RING " + self.app.config["spawnedby"] + "\n")
		if command == "CLIENTBATTLESTATUS" and len(args) > 0 and self.redirectbattleroom:
			pm(s,self.app.config["spawnedby"], "!" + command + " " + " ".join(args[0:]) )
		if command == "SAIDBATTLE" and len(args) > 0:
			if self.redirectbattleroom:
				pm(s,self.app.config["spawnedby"], "!" + command + " " + " ".join(args[0:]))
			if args[1].startswith("!") and args[0] == self.battleowner:
				try:
					msg = " ".join(args[1:])
					self.u.sayingame("/"+msg[1:])
				except:
					exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
					loge(socket,"*** EXCEPTION: BEGIN")
					for line in exc:
						loge(self.sock,line)
		if command == "SAIDBATTLEEX" and len(args) > 0 and self.redirectbattleroom:
			pm(s,self.app.config["spawnedby"], "!" + command + " " + " ".join(args[0:]))
		if command == "REQUESTBATTLESTATUS":
			s.send( "MYBATTLESTATUS 4194816 255\n" )#spectator+synced/white
		if command == "SAIDPRIVATE" and args[0] not in self.app.config["bans"] and args[0] == self.app.config["spawnedby"]:
			if args[1] == "!openbattle" and not self.hosted == 1:
				if len(args) < 6:
					Log.Error("Got invalid openbattle with params:"+" ".join(args))
					return
				args[5] = self.app.config["hostport"]
				Log.Info("OPENBATTLE "+" ".join(args[2:]))
				s.send("OPENBATTLE "+" ".join(args[2:])+"\n")
				self.battleowner = args[0]
				return
			elif args[1] == "!openbattle" and self.hosted == 1:
				pm(s,args[0],"E1 | Battle is already hosted")
				return
			elif args[1] == "!supportscriptpassword":
				self.redirectjoins = True
				return
			elif self.hosted == 1 and args[0] == self.battleowner:
				if args[1] == "!setingamepassword":
					try:
						msg = " ".join(args[2:])
						self.u.sayingame("/adduser "+msg)
					except:
						exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
						loge(socket,"*** EXCEPTION: BEGIN")
						for line in exc:
							loge(self.sock,line)
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
						if ( self.tsc.users[self.battleowner].bot ):
							self.redirectspring = bool(args[2])
					except:
						exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
						loge(socket,"*** EXCEPTION: BEGIN")
						for line in exc:
							loge(self.sock,line)
						loge(socket,"*** EXCEPTION: END")
				if args[1] == "!redirectbattleroom"and len(args) > 1:
					try:
						if ( self.tsc.users[self.battleowner].bot ):
							self.redirectbattleroom = bool(args[2])
					except:
						exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
						loge(socket,"*** EXCEPTION: BEGIN")
						for line in exc:
							loge(self.sock,line)
						loge(socket,"*** EXCEPTION: END")
				if args[1] == "!cleanscript":
					self.script = ""
				if args[1] == "!appendscriptline":
					self.script += " ".join(args[2:])+"\n"
				if args[1].startswith("#") and args[0] == self.battleowner:
					try:
						msg = " ".join(args[1:])
						self.u.sayingame(msg[1:])
					except:
						exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
						loge(socket,"*** EXCEPTION: BEGIN")
						for line in exc:
							loge(self.sock,line)
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
						except:
							pass
						f = open(os.path.join(self.scriptbasepath,"%f.txt" % g),"a")
						s1 = self.script.find("MyPlayerName=")
						s2 = self.script[s1:].find(";")+1+s1
						self.script = self.script.replace(self.script[s1:s2],"MyPlayerName=%s;\n\tAutoHostPort=%i;" % (self.app.config["nick"],int(self.app.config["ahport"])))
						s1 = self.script.find("HostIP=")
						s2 = self.script[s1:].find(";")+1+s1
						if "bindip" in self.app.config:
							self.script = self.script.replace(self.script[s1:s2],"HostIP=%s" % (self.app.config["bindip"]))
						else:
							self.script = self.script[0:s1] + self.script[s2:]
						f.write(self.script)
						f.close()
						thread.start_new_thread(self.startspring,(s,g))
					else:
						pm(s,args[0],"E3 | Battle already started")
			else:
				pm(s,args[0],"E2 | Battle is not hosted")

		if command == "OPENBATTLE":
			self.battleid = int(args[0])
			self.used = 1
			loge(s,"Battle hosted succesfully , id is %s" % args[0])
		if command == "JOINEDBATTLE" and len(args) >= 2 and int(args[0]) == self.battleid:
			if args[1] == self.battleowner:
				self.hosted = 1
				self.noowner = False
				loge(s,"The host has joined the battle")
				s.send("SAYBATTLE Hello, the bot accepts all commands from normal spring prefixed with ! instead of /\n")
				s.send("SAYBATTLE read Documentation/cmds.txt for a list of spring commands\n")
				s.send("SAYBATTLE in order to stop a game immediately, use !kill\n")
			if self.redirectjoins:
				pm(s,self.battleowner,command + " " + " ".join(args[0:])) # redirect the join command to the owner so he can manage script password
		if command == "SERVERMSG":
			pm(s,self.battleowner," ".join(args))
		if command == "LEFTBATTLE" and int(args[0]) == self.battleid and args[1] == self.battleowner:
			if	not self.gamestarted:
				loge(s,"The host has left the battle and the game isn't running, exiting")
				s.send("LEAVEBATTLE\n")
				try:
					if platform.system() == "Windows":
						handle = win32api.OpenProcess(1, 0, self.pr.pid)
						win32api.TerminateProcess(handle, 0)
					else:
						os.kill(self.pr.pid,signal.SIGKILL)
				except:
					pass
				self.killbot()

			self.noowner = True

		if command == "REMOVEUSER" and args[0] == self.battleowner:
			if	not self.gamestarted:
				loge(s,"The host disconnected and game not started, exiting")
				try:
					if platform.system() == "Windows":
						handle = win32api.OpenProcess(1, 0, self.pr.pid)
						win32api.TerminateProcess(handle, 0)
					else:
						os.kill(self.pr.pid,signal.SIGKILL)
				except:
					pass
				self.killbot()
			self.noowner = True

	def onloggedin(self,socket):
		self.noowner = True
		self.hosted = 0
		if self.gamestarted:
			socket.send("MYSTATUS 1\n")

