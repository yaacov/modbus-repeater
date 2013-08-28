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

import sys
import time
import datetime
import argparse

from socket import socket, AF_INET, SOCK_STREAM
from serial import Serial
from struct import pack, unpack
from thread import start_new_thread

try:
    from pyca.ca_com_utils import *
except:
    pass

# Serial port communication
class SerialTal():
    ''' Serial port with partial tal functionality
        with response cache
        
        using pyca, tal serial communication python module
        
        Available tal functions:
            0x03: read holding registers
            0x04: read input registers
            0x10: write input registers
    '''
    def __init__(self, tal_addr):
        self.cache = {}
        self.com = create_com('tal://%s/' % tal_addr)
        self.cache_validity_time = 1 # cache is valid for 1 sec
    
    def check_cache(self, key):
        ''' check cached value for a key'''
        timestamp = time.time()
        validity_time = timestamp - self.cache_validity_time
        
        if (key in self.cache.keys() and 
                self.cache[key]['timestamp'] > validity_time):
            ans = self.cache[key]['response']
        else:
            raise Exception('Cache fail')
        
        return ans
        
    def update_cache(self, key, value):
        ''' update cache with a value'''
        timestamp = time.time()
        
        self.cache[key] = {'timestamp': timestamp, 'response': value}
        
    def get_holding_registers(self, unit, addr, count):
        ''' get holding registers from a tal unit

        unit -- modbus unit number
        addr -- start addres
        count -- number of registers to read
        '''
        
        return self.get_registers(unit, addr, count, command = 0x03)
    
    def get_input_registers(self, unit, addr, count):
        ''' get input registers from a tal unit

        unit -- modbus unit number
        addr -- start addres
        count -- number of registers to read
        '''
        
        return self.get_registers(unit, addr, count, command = 0x04)
    
    def get_registers(self, unit, addr, count, command = 0x04):
        ''' get registers from a tal unit

        unit -- modbus unit number
        addr -- start addres
        count -- number of registers to read
        command -- modbus command
        '''
        # check cache
        key = '%03d%04d%04d%d' % (unit, addr, count, command)
        try:
            # if we have an answer in cache, return it
            ans = check_cache(key)
            return ans
        except:
            # blank response, and continue
            ans = None
        
        # get items from unit
        items = range(int(addr / 2) + 1, int((addr + count) / 2) + 1)
        try:
            response = self.com.get_par(0, unit, items)
        except:
            responce = None
        
        # tal use parameters and not registers. command 3 in tal mean
        # answer is in unsigned ints, command 4 in tal mean answer is float
        if response:
            if command == 0x03:
                data = []
                for item in response: data += [item, item]
                
                ans = pack(">%dH" % count, *data)
            elif command == 0x04:
                ans = pack(">%df" % (count / 2), *response)
            
            # update the cache
            self.update_cache(key, ans)
        
        return ans
    
    def set_input_registers(self, unit, addr, count, registers):
        ''' set registers from in a tal unit

        unit -- modbus unit number
        addr -- start addres
        count -- number of registers to read
        registers -- a packed data to write
        '''
        # get the items to write
        item = int(addr / 2) + 1
        reg_count = 0
        byte_index = 0
        
        try:
            # tal can only write one float at a time 
            while reg_count < count:
                self.com.set_par(0, unit, item, 
                    unpack(">f", registers[byte_index:(byte_index + 4)]))
                    
                # one float item is 2 registers (4 bytes)
                item += 1
                reg_count += 2
                byte_index += 4
        except:
            pass
        
        # return addr and number of registers writen
        return [addr, reg_count]

# Serial port communication
class SerialModbus(Serial):
    ''' Serial port with partial modbus functionality
        with response cache
        
        usint pyserial, serial port python module
        
        Available modbus functions:
            0x03: read holding registers
            0x04: read input registers
            0x10: write input registers
    '''
    cache = {}
    cache_validity_time = 1 # cache is valid for 1 sec
    
    def check_cache(self, key):
        ''' check cached value for a key'''
        timestamp = time.time()
        validity_time = timestamp - self.cache_validity_time
        
        if (key in self.cache.keys() and 
                self.cache[key]['timestamp'] > validity_time):
            
            ans = self.cache[key]['response']
        else:
            raise Exception('Cache fail')
        
        return ans
        
    def update_cache(self, key, value):
        ''' update cache with a value'''
        timestamp = time.time()
        
        self.cache[key] = {'timestamp': timestamp, 'response': value}
        
    def swap_bytes(self, word_val):
        ''' swap lsb and msb of a word '''
        msb = word_val >> 8
        lsb = word_val % 256
        return (lsb << 8) + msb
        
    def calc_crc16(self, data):
        ''' calculate 16 bit CRC of a datagram '''
        crc = 0xFFFF
        for i in data:
            crc = crc ^ ord(i)
            for j in xrange(8):
                tmp = crc & 1
                crc = crc >> 1
                if tmp:
                    crc = crc ^ 0xA001

        return pack('>H', self.swap_bytes(crc))
    
    def get_holding_registers(self, unit, addr, count):
        ''' get holding registers from a modbus unit

        unit -- modbus unit number
        addr -- start addres
        count -- number of registers to read
        '''
        
        return self.get_registers(unit, addr, count, command = 3)
    
    def get_input_registers(self, unit, addr, count):
        ''' get input registers from a modbus unit

        unit -- modbus unit number
        addr -- start addres
        count -- number of registers to read
        '''
        
        return self.get_registers(unit, addr, count, command = 4)
    
    def get_registers(self, unit, addr, count, command = 4):
        ''' get registers from a modbus unit

        unit -- modbus unit number
        addr -- start addres
        count -- number of registers to read
        command -- the modbus command to use
        '''
        # check cache
        key = '%03d%04d%04d%d' % (unit, addr, count, command)
        try:
            # if we have an answer in cache, return it
            ans = check_cache(key)
            return ans
        except:
            # blank response, and continue
            ans = None
        
        # make sure no leftovers in buffers
        self.flushInput()
        self.flushOutput()
        
        # build modbus request
        msg = pack('>2B2H', unit, command, addr, count)
        msg = msg + self.calc_crc16(msg)
        self.write(msg)
        
        # wait for answer (do not check CRC)
        answer_length = 3 + count * 2
        replay = self.read(answer_length)
        
        # if we have and answer, update the cache
        if len(replay) == answer_length:
            ans = replay[3:]
            self.update_cache(key, ans)
            
        return ans
    
    def set_input_registers(self, unit, addr, count, registers):
        ''' set registers from in a modbus unit

        unit -- modbus unit number
        addr -- start addres
        count -- number of registers to read
        registers -- a packed data to write
        '''
        
        ans = [0, 0,]
        command = 0x10
        answer_length = 8
        
        # make sure no leftovers in buffers
        self.flushInput()
        self.flushOutput()
        
        # build modbus request
        msg = pack('>2B2HB', unit, command, addr, count, count * 2) + registers
        msg = msg + self.calc_crc16(msg)
        self.write(msg)
        
        # wait for answer (do not check CRC)
        replay = self.read(answer_length)
        
        # if we have and answer, get the addr and number of registers
        if len(replay) == answer_length:
            ans = unpack(">2H", replay[4:])
            
        return ans

# Modbus tcp->serial repeater
class ModbusRepeater:
    ''' A TCP/IP Modbus server, the server listen to modbus requests
        On port 502/tcp and repeat them on a serial port.
        
        Available modbus functions:
            0x03: read holding registers
            0x04: read input registers
            0x10: write input registers
    '''
    
    def __init__(self, soc, backend):
        ''' init the repeater interfaces
        '''
        
        # a tcp/ip socket, listening on port 502/tcp
        self.soc = soc 
        
        # a serial port
        # implementing:
        #    get_input_registers
        #    get_holding_registers
        #    set_input_registers
        self.backend = backend
    
    def dump_registers(self, registers):
        ''' dump registers to console
        '''
        print "Registers"
        for c in registers:
            print hex(ord(c)),
        print
        
    def handle(self, conn, addr, debug = False):
        ''' handle one modbus connection
        '''
        if debug: print 'Connected by', addr
        
        # repeat until connection is closed
        while True:
            # read new data
            data = conn.recv(1024)
            if not data:
                break
            
            # parse the new request
            try:
                packat_id, protocol, length, unit, command = unpack(">3H2B", data[:8])
            except Exception, e:
                if debug: print "Bad request"
                break
            
            # if command is write input/holding registers, try to write serial/tal port
            if command in [0x10,]:
                # get request data
                addr, count, bytes = unpack(">2HB", data[8:13])
                if debug: print "unit=%d addr=%d count=%d (%d)" % (unit, addr, count, command)
                
                # get request values to write
                registers = data[13:]
                if debug: self.dump_registers(registers)
                
                ans_addr, ans_count = self.backend.set_input_registers(unit, addr, count, registers)
                
                # return the addres and number of registers writen
                conn.send(pack(">3H2B2H", packat_id, protocol, 
                    count * 2 + 3, unit, command, ans_addr, ans_count))
                
            # if command is read input/holding registers, try to read serial/tal port
            if command in [0x03, 0x04]:
                # get request data
                addr, count = unpack(">2H", data[8:])
                if debug: print "unit=%d addr=%d count=%d (%d)" % (unit, addr, count, command)
                
                # try to read registers using the serial backend
                registers = None
                try:
                    if command == 0x03:
                        registers = self.backend.get_holding_registers(unit, addr, count)
                    elif command == 0x04:
                        registers = self.backend.get_input_registers(unit, addr, count)
                except Exception, e:
                    if debug: print "Bad backend response"
                    break
                    
                if registers:
                    if debug: self.dump_registers(registers)
                    
                    conn.send(pack(">3H3B", packat_id, protocol, 
                        count * 2 + 3, unit, command, count * 2) + registers)
        
        conn.close()
        if debug: print "Connection closed"
    
    def run(self, debug=False):
        ''' serve forever function
        '''
        # serve forever
        while True:
            # wait for a new request
            conn, addr = self.soc.accept()
            
            # respond in a new thread
            start_new_thread(self.handle, (conn, addr, debug))

def main():
    ''' get user arguments and run the modbus repeater
    '''
    parser = argparse.ArgumentParser(description='Modbus TCP to Serial repeater.')
    
    parser.add_argument('-l', dest='tcp_port',
                       type=int, default=502,
                       help='ip port to listen (default: 502)')
    parser.add_argument('-b', dest='baudrate',
                       type=int, default=38400,
                       help='serial port baudrate (default: 38400)')
    parser.add_argument('-p', dest='parity',
                       type=str, default='E',
                       help='serial port parity (default: E)')
    parser.add_argument('-c', dest='port',
                       type=str, default='COM1',
                       help='serial port com-port')
    parser.add_argument('-t', dest='tal',
                       default=False,
                       help='serial port tal addr')
    parser.add_argument('-d', dest='debug', action='store_const',
                       const=True, default=False,
                       help='print debug information')
    args = parser.parse_args()
    
    # serial port
    if args.tal:
        ser = SerialTal(args.tal)
    else:
        ser = SerialModbus(port=args.port, 
            baudrate=args.baudrate, bytesize=8, parity=args.parity, stopbits=1)
        
    # TCP/IP socket
    HOST = "0.0.0.0"
    PORT = args.tcp_port
    
    soc = socket(AF_INET, SOCK_STREAM)
    soc.bind((HOST, PORT))
    soc.listen(1)
    
    # print message
    print
    print "Modbus TCP to Serial repeater"
    print "-----------------------------"
    print "listen on tcp port:", PORT
    
    if args.tal:
        print "use tal:           ", args.tal
    else:
        print "serial port:       ", args.port
        print "serial baudrate:   ", args.baudrate
        print "serial parity:     ", args.parity
        
    print "start time is:     ", datetime.datetime.now()
    print
    print "press Ctrl+C to exit"
    print
    
    # run the repeater
    m = ModbusRepeater(soc, ser)
    m.run(debug=args.debug)

if __name__ == '__main__':
    main()

