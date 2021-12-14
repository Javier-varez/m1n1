#!/usr/bin/env python3

import sys, pathlib, traceback
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.proxy import *
from m1n1.proxyutils import *
from m1n1.utils import *
from m1n1.shell import run_shell
from m1n1.hv import HV

iface = UartInterface()
p = M1N1Proxy(iface, debug=False)
bootstrap_port(iface, p)
u = ProxyUtils(p, heap_size = 128 * 1024 * 1024)

hv = HV(iface, p, u)

hv.init()

payload = pathlib.Path("/home/javier/Documents/code/p1c0/fw/p1c0.macho")

hv.load_macho(payload.open("rb"))
hv.start()
# hv.run_shell()
