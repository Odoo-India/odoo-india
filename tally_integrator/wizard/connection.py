import httplib
from osv import osv 


def make_connection(self, url="localhost:9000"):
	try:
		conn = httplib.HTTPConnection(url)
	except Exception:
		raise osv.except_osv(('Error !'), ('Error Occured While Connecting With Tally.'))
	return conn

