#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib
import time
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import os.path
import code
import sys

from m1n1.setup import *
from m1n1.hw.dart import DART, DARTRegs
from m1n1.hw.admac import ADMAC, ADMACRegs
from m1n1.hw.i2c import I2C

class Tps6598x:
    CMD_REG = 0x08
    DATA_REG = 0x09

    INVALID_CMD = 0x21434d44

    def __init__(self, i2c, addr):
        self.i2c = i2c
        self.addr = addr

    def read_reg(self, reg, size):
        # The raw i2c reg functions include the length of the transfer as the first argument
        return self.i2c.read_reg(self.addr, reg, size + 1)[1:]

    def write_reg(self, reg, data):
        # The raw i2c reg functions include the length of the transfer as the first argument
        return self.i2c.write_reg(self.addr, reg, [len(data)] + data)

    def read_reg32(self, reg):
        data = self.read_reg(reg, 4)
        assert len(data) == 4
        return data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)

    def exec_cmd(self, cmd, data_in, out_len):
        v = self.read_reg32(self.CMD_REG)
        if  v != 0 and v != self.INVALID_CMD:
            raise Exception("Command already in progress")

        if data_in:
            self.write_reg(self.DATA_REG, data_in)

        cmd = list(map(ord, cmd))
        self.write_reg(self.CMD_REG, cmd)

        v = self.read_reg32(self.CMD_REG)
        while v != 0:
            if v == 0x21434d44:  # !CMD
                raise Exception("Invalid command!")
            v = self.read_reg32(self.CMD_REG)

        if not out_len:
            return

        return self.read_reg(self.DATA_REG, out_len)

    def read_mode(self):
        return str(self.read_reg(0x03, 4))

if __name__ == "__main__":
    p.pmgr_adt_clocks_enable("/arm-io/i2c0")
    i2c0 = I2C(u, "/arm-io/i2c0")
    i2c_addr = u.adt["/arm-io/i2c0/hpmBusManager/hpm0"].hpm_iic_addr

    tps = Tps6598x(i2c0, i2c_addr)

    print(f"state {tps.read_mode()}")

    tps.exec_cmd("DBMa", [1], 0)
    print(f"state {tps.read_mode()}")

    tps.exec_cmd("DBMa", [0], 0)
    print(f"state {tps.read_mode()}")
