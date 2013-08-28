#!/usr/bin/env python
# -*- coding:utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# Copyright (C) 2013 Yaacov Zamir <kobi.zamir@gmail.com>
# Author: Yaacov Zamir (2013)

''' mbs-client

A modbus client
'''

import sys
import time
import datetime
import socket
import argparse
from struct import pack, unpack
from struct import error as StructError

def write_registers(soc, unit, addr, value,
        display_format = 'int', command = 0x10):
    ''' write input registers to a modbus unit
    '''

    # check if value is float or int
    if display_format == 'float':
        message = pack(">3H2B2HBf", 1, 0, 11, unit, command, addr, 2, 4, value)
    else:
        message = pack(">3H2B2HBH", 1, 0, 9, unit, command, addr, 1, 2, value)

    soc.send(message)
    replay = soc.recv(1024)

    # parse response: adress and count
    try:
        data = unpack('>2H', replay[8:])
    except Exception, e:
        # replay is None
        data = "Err"

    timestamp = datetime.datetime.now()

    # print out the data
    print timestamp, data

    return

def read_registers(soc, unit, addr, count,
        display_format = 'int', command = 0x04):
    ''' read input registers from modbus unit
    '''

    message = pack(">3H2B2H", 1, 0, 6, unit, command, addr, count)
    soc.send(message)
    replay = soc.recv(1024)

    # parse response as float/int
    try:
        if display_format == 'float':
            data = unpack('>%df' % (count / 2), replay[9:])
        else:
            data = unpack('>%dH' % count, replay[9:])
    except Exception, e:
        data = ("Err",)

    timestamp = datetime.datetime.now()

    # print out the data
    print ",".join([str(el) for el in (timestamp,) + data])

    return

def main():
    ''' get user arguments and run the modbus reader
    '''
    commands = {}
    commands[0x03] = 'read holding register'
    commands[0x04] = 'read input register'
    commands[0x10] = 'write input register'

    parser = argparse.ArgumentParser(description='Modbus TCP reader.')

    parser.add_argument('-l', dest='tcp_port',
                       type=int, default=502,
                       help='ip port to use (default: 502)')
    parser.add_argument('-i', dest='tcp_ip',
                       default='127.0.0.1',
                       help='ip of server unit')
    parser.add_argument('-n', dest='unit_number',
                       type=int, default=1,
                       help='unit number')
    parser.add_argument('-a', dest='adress',
                       type=int, default=1,
                       help='register start adress (first adress is 1)')
    parser.add_argument('-c', dest='count',
                       type=int, default=2,
                       help='number of registers to read')
    parser.add_argument('-t', dest='timeout',
                       type=int, default=False,
                       help='repeat readings evry N sec')
    parser.add_argument('-f', dest='display_format', action='store_const',
                       const='int', default='float',
                       help='parse values as int (default is float)')
    parser.add_argument('-v', dest='value',
                       type=float, default=0,
                       help='value to write to register')
    parser.add_argument('-r', dest='command',
                       type=int,
                       choices=[3, 4, 16],
                       default=4,
                       help='''modbus command''')
    args = parser.parse_args()

    # print message
    print
    print "Modbus TCP register reader"
    print "--------------------------"
    print "tcp port (-l):                   ", args.tcp_port
    print "unit ip: (-i)                    ", args.tcp_ip
    print "unit number: (-n)                ", args.unit_number
    print "start adress: (-a)               ", args.adress
    print "number or registers to read: (-c)", args.count

    if args.command in [0x10,]:
        print "write value:                     ", args.value

    print "modbus command: (-r)             ", commands[args.command]
    print "display format: (-f)             ", args.display_format

    if args.command in [0x3, 0x04] and args.timeout:
        print "repeat evry N sec: (-t)          ", args.timeout

    print

    # adress start with zero
    args.adress -= 1

    # open socket
    try:
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((args.tcp_ip, args.tcp_port))
    except socket.error:
        print "Err: can't open socket"
        sys.exit(1)

    # write input registers
    if args.command in [0x10,]:
        write_registers(soc,
            args.unit_number, args.adress, args.value,
            args.display_format, args.command)

    # read input registers
    elif args.command in [0x03, 0x04]:
        read_registers(soc,
            args.unit_number, args.adress, args.count,
            args.display_format, args.command)

        # if user enterd timeout, repeat readings
        while args.timeout:
            # get new data from unit
            read_registers(soc,
                args.unit_number, args.adress, args.count,
                args.display_format, args.command)

            # sleep
            time.sleep(args.timeout)

    print
    soc.close()

if __name__ == '__main__':
    main()

