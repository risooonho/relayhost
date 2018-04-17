import socket
from tasbot.customlog import Log
import thread
import string
import traceback,sys
class UDPint:
	def __init__(self,port,messagecb,eventcb):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s.settimeout(5.0)
		self.addr = ("localhost",int(port))
		self.s.bind(self.addr)
		self.players = dict()
		self.running = True
		self.port = port
		thread.start_new_thread(self.mainloop,(messagecb,eventcb))
		Log.info("UDP Listening on port "+str(port))

	def reset(self):
		self.players = dict()

	def mainloop(self,messagecb,eventcb):
		try:
			while self.running:
				try:
					data, address = self.s.recvfrom(8192)
				except socket.timeout:
					if self.running:
						continue
					else:
						break
				self.addr = address
				event = ord(data[0])
				#print "Received event %i from %s" % (event,str(address))
				if event == 10:
					n = ord(data[1])
					name = data[2:]
					self.players.update([(n,name)])
				if event == 13:
					n = ord(data[1])
					text = data[3:]
					if not text.lower().startswith("a:"):
						messagecb(self.players[n],text)
				if event == 3: #gameover
					self.sayingame("/kill")
				eventcb(ord(data[0]),data[1:])
		except Exception, e:
			Log.exception( e )
		self.logger.info( "Closing autohost interface %d" %(self.port) )
		self.s.close()

	def sayingame(self,text):
		#print "Sending %s to spring" % text
		try:
			self.s.sendto(text,self.addr)
		except Exception, e:
			Log.exception( e )
