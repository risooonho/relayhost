from tasbot.ParseConfig import *
from tasbot.Plugin import IPlugin

class Main(IPlugin):
	def __init__(self,name,tasclient):
		IPlugin.__init__(self,name,tasclient)
	def onload(self,tasc):
		pass
	def oncommandfromserver(self,command,args,socket):
		if command == "SAIDPRIVATE" and len(args) > 1 and args[1] == "!lag":
			self.tasclient.socket("SAYPRIVATE %s %s\n" % ( args[0], str((self.app.lpo-self.app.lp)*1000) +" ms"))
