
import os

class DefaultConfig(object):
    """
    Default OE Connection configuration Params
    """
    OPENERP_DEFAULT_USER_NAME = 'admin'
    OPENERP_DEFAULT_PASSWORD = 'a'
    OPENERP_HOSTNAME = '127.0.0.1'
    OPENERP_PORT = 8069
    OPENERP_DEFAULT_DATABASE = 'dbname'
    PATH = False
    user = os.getlogin()
    DEFAULT_PATH="/home/"+user+"/Desktop/script/"

config = DefaultConfig()
