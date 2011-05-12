import httplib
from osv import osv 

def make_connection(self,url="localhost:9000"):
	try:
		conn = httplib.HTTPConnection(url)
	except:
		raise osv.except_osv(('Error !'), ('Error occured while connecting with Tally.'))
	return conn
