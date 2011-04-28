from tasbot.Plugin import IPlugin

class Main(IPlugin):
	def __init__(self,name,tasclient):
		IPlugin.__init__(self,name,tasclient)
	def onload(self,tasc):
		pass
	def oncommandfromserver(self,command,args,socket):
		pass
	def onloggedin(self,socket):
		socket.send("JOIN autohost\n")
