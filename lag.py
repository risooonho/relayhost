from tasbot.ParseConfig import *
from tasbot.Plugin import IPlugin

class Main(IPlugin):
	def __init__(self,name,tasclient):
		IPlugin.__init__(self,name,tasclient)
		self.sock = None
		self.app = None
	def onload(self,tasc):
		self.app = tasc
	def oncommandfromserver(self,command,args,socket):
		if command == "SAIDPRIVATE" and len(args) > 1 and args[1] == "!lag":
			socket.send("SAYPRIVATE %s %s\n" % ( args[0], str((self.app.lpo-self.app.lp)*1000) +" ms"))
	def onloggedin(self,socket):
		pass

