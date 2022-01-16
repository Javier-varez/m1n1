#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib, traceback
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import argparse, pathlib

parser = argparse.ArgumentParser(description='Run a Mach-O payload under the hypervisor')
parser.add_argument('-s', '--symbols', type=pathlib.Path)
parser.add_argument('-l', '--logfile', type=pathlib.Path)
parser.add_argument('payload', type=pathlib.Path)
parser.add_argument('boot_args', default=[], nargs="*")
args = parser.parse_args()

from m1n1.proxy import *
from m1n1.proxyutils import *
from m1n1.utils import *
from m1n1.hv import HV
from m1n1.gpiola import GPIOLogicAnalyzer

iface = UartInterface()
p = M1N1Proxy(iface, debug=False)
bootstrap_port(iface, p)
u = ProxyUtils(p, heap_size = 128 * 1024 * 1024)

hv = HV(iface, p, u)
# Disable SMP in the HYP since we need to run the logic analyzer in another CPU
hv.smp = False

# Start other cores so that we can load the GPIO Logic Analyzer
p.smp_start_secondaries()

trace_pins = {
    "miso": 0x34,
    "mosi": 0x35,
    "clk": 0x36,
    "cs": 0x37
}

spi = u.adt["arm-io/spi3"].get_reg(0)[0]
regs = {
    "IF_FIFO": (spi + 0x13C),
    "FIFO_STATUS": (spi + 0x10C),
    "STATUS": (spi + 0x08),
    "CTRL": (spi + 0x00),
    "PIN": (spi + 0x0C),
    "RXCNT": (spi + 0x34),
    "TXCNT": (spi + 0x4c),
}

logic_analyzer = GPIOLogicAnalyzer(u, "arm-io/gpio0", pins=trace_pins, on_pin_change=False, regs=regs)
hv.shell_locals.update({'logic_analyzer': logic_analyzer})

hv.init()
if args.logfile:
    hv.set_logfile(args.logfile.open("w"))

hv.load_macho(args.payload.open("rb"))

logic_analyzer.start(300000, bufsize=0x800000)
hv.start()

# Don't forget to call logic_analyzer.complete()
# And then logic_analyzer.show()
