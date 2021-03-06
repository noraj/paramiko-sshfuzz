import logging
logging.basicConfig(loglevel=logging.DEBUG)
logging.getLogger("paramiko.fuzz").setLevel(logging.INFO)

import paramiko.fuzz
import paramiko
from paramiko import util, common
from paramiko import Message
import struct
zero_byte = '\x00'
one_byte = '\x01'
max_byte = '\xff'

import random

def add_bytes(self, b):
    """
    Write bytes to the stream, without any formatting.
    
    :param str b: bytes to add
    """
    self.packet.write(b)
    return self

def add_byte(self, b):
    """
    Write a single byte to the stream, without any formatting.
    
    :param str b: byte to add
    """
    self.packet.write(b)
    return self

def add_boolean(self, b):
    """
    Add a boolean value to the stream.
    
    :param bool b: boolean value to add
    """
    if random.choice([False]*7+[True]):
        b = random.choice(xrange(2,0xff))
        self.packet.write(str(b))
    else:
        if b:
            self.packet.write(one_byte)
        else:
            self.packet.write(zero_byte)
    return self
        
def add_int(self, n):
    """
    Add an integer to the stream.
    
    :param int n: integer to add
    """
    if random.choice([False]*7+[True]):
        n = random.choice([0,0xffffffff,0xffffffff/2])
        
    self.packet.write(struct.pack('>I', n))
    return self
        
def add_adaptive_int(self, n):
    """
    Add an integer to the stream.
    
    :param int n: integer to add
    """
    if n >= Message.big_int:
        self.packet.write(max_byte)
        self.add_string(util.deflate_long(n))
    else:
        self.packet.write(struct.pack('>I', n))
    return self

def add_int64(self, n):
    """
    Add a 64-bit int to the stream.

    :param long n: long int to add
    """
    self.packet.write(struct.pack('>Q', n))
    return self

def add_string(self, s):
    """
    Add a string to the stream.
    
    :param str s: string to add
    """
    s = common.asbytes(s)
    if random.choice([False]*7+[True]):
        self.add_int(0xffffffff)
    else:
        self.add_int(len(s))
    self.packet.write(s)
    return self

FuzzMaster = paramiko.fuzz.FuzzMaster
FuzzMaster.MUTATION_PER_RUN=10000
#FuzzMaster.add_fuzzdef("add_byte",add_byte)
FuzzMaster.add_fuzzdef("add_string",add_string)
FuzzMaster.add_fuzzdef("add_int",add_int)
FuzzMaster.add_fuzzdef("add_boolean",add_boolean)
#FuzzMaster.add_fuzzdef("add_adaptive_int",add_adaptive_int)
#FuzzMaster.add_fuzzdef("add_int64",add_int64)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
for i in xrange(100):
    try:
        client.connect(hostname="host", port=22, 
                         username="user", password="password")
        _, sout, _ = client.exec_command("whoami")
        print sout.read()
        _, sout, _ = client.exec_command("whoami")
        print sout.read()
        client.invoke_shell()
        client.open_sftp()
        transport = client.get_transport()
        session = transport.open_session()
        session.request_x11(auth_cookie="JO")
        session.exec_command("whoami")
    except paramiko.fuzz.StopFuzzing, sf:
        print "STOP FUZZING"
        
        break
    except Exception, e:
        print repr(e)