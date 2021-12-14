#!/usr/bin/env python3

import sys, pathlib, traceback
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.proxy import *
from m1n1.proxyutils import *
from m1n1.utils import *
from m1n1.shell import run_shell
from m1n1.hv import HV, HV_EVENT

iface = UartInterface()
p = M1N1Proxy(iface, debug=False)
bootstrap_port(iface, p)
u = ProxyUtils(p, heap_size = 128 * 1024 * 1024)

PA_MASK = (1 << 48) - (1 << 14)
TYPE_MASK = (1 << 55) | (1 << 1) | (1 << 0)
TYPE_PAGE = TYPE_MASK
TYPE_TABLE = (1 << 1) | (1 << 0)
BLOCK_MASK = (1 << 1) | (1 << 0)
TYPE_BLOCK = (0 << 1) | (1 << 0)
VALID_MASK = 1 << 0

def is_valid(entry):
    return (entry & VALID_MASK) != 0

def is_table(entry):
    if is_valid(entry):
        return (entry & TYPE_MASK) == TYPE_TABLE
    return False

def is_page(entry):
    if is_valid(entry):
        return (entry & TYPE_MASK) == TYPE_PAGE
    return False

def is_block(entry):
    if is_valid(entry):
        return (entry & BLOCK_MASK) == TYPE_BLOCK
    return False

def get_pa(entry):
    return entry & PA_MASK

def print_entry_type(entry):
    if not is_valid(entry):
        return

    if is_table(entry):
        print(f'\tTable entry pointing to: 0x{get_pa(entry):x}')
    elif is_page(entry):
        print(f'\tPage entry pointing to: 0x{get_pa(entry):x}')
    elif is_block(entry):
        print(f'\tBlock entry pointing to: 0x{get_pa(entry):x}')

def print_l3_table(l3_table_addr, base_addr):
    for i in range(2048):
        entry = p.read64(l3_table_addr + (8 * i))
        if is_valid(entry):
            va = base_addr + (1 << 25) * i
            print(f'Table 3 entry {i}: va -> 0x{va:x}')
            print_entry_type(entry)
            if is_table(entry):
                print("Found table in L3!!!!!!!!")

def print_l2_table(l2_table_addr, base_addr):
    for i in range(2048):
        entry = p.read64(l2_table_addr + (8 * i))
        if is_valid(entry):
            va = base_addr + (1 << 25) * i
            print(f'Table 2 entry {i}: va -> 0x{va:x}')
            print_entry_type(entry)
            if is_table(entry):
                print_l3_table(get_pa(entry), va)

def print_l1_table(l1_table_addr, base_addr):
    for i in range(2048):
        entry = p.read64(l1_table_addr + (8 * i))
        if is_valid(entry):
            va = base_addr + (1 << 36) * i
            print(f'Table 1 entry {i}: va -> 0x{va:x}')
            print_entry_type(entry)
            if is_table(entry):
                print_l2_table(get_pa(entry), va)

def print_vm_tables(l0_table_addr):
    print(f'Table 0 address is 0x{l0_table_addr:x}')
    for i in range(2):
        entry = p.read64(l0_table_addr + (8 * i))
        if is_valid(entry):
            print(f'Table 0 entry {i}')
            print_entry_type(entry)
            print(f'found L0 entry at {entry:x}')
            print_l1_table(get_pa(entry), (1 << 47) * i)

def vm_trap(reason, code, info):
    print(f'my trap is running {reason}, {code}, {info}')
    table0 = u.mrs('TTBR0_EL12')
    print_vm_tables(table0)
    p.exit(EXC_RET.HANDLED)
    # hv.run_shell()

iface.set_handler(START.VM, HV_EVENT.USER_INTERRUPT, vm_trap)

hv = HV(iface, p, u)

hv.init()

payload = pathlib.Path("/home/javier/Documents/code/p1c0/fw/p1c0.macho")

hv.load_macho(payload.open("rb"))
hv.start()
# hv.run_shell()
