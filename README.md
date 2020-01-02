# paramiko-sshfuzz

See [README](README) for the paramiko readme.

Paramiko based SSH fuzzer that hooks into paramiko.message raw message packing functionality to fuzz the ssh protocol.
It is based on a decorator driven fuzzing controller. Methods that should be tracked and intercepted are registered to 
the fuzzing controller `paramiko.fuzz.FuzzMaster` by decorathing them with `@paramiko.fuzz.FuzzMaster.candidate`. To actually
start fuzzing a `fuzzing_corpus` has to be created. This is basically a valid ssh scenario where the fuzzing controller is 
initialized and a few mutation methods for the decorated candidates are defined. An good corpus should try to use all the paramiko 
offered ssh features.
Whenever the test corups calls a candidate function, control is handed to the fuzzing controller which then calls the method 
specific fuzzing method. This is typically the original function with some random or deterministic factor and some changes to generically inject
faults.

the fuzzing controller keeps track of unique call graphs in order to exhaustively fuzz every single candidate function.


For a working example see demos/fuzzing_corpus.py

1. get a `paramiko.fuzz.FuzzMaster` reference
2. assign your fuzzing function to on of the `paramiko.message` fuzzpoints. 
In this case we're defining an `add_string` function that adds an invalid
length-prefix to the raw ssh-string on a random basis.

```
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
```
	
```python
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
```
