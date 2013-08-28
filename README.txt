Modbus repeater
---------------

Modbus repeater is a python script that listen for modbus requests on a tcp connection 
and repeat the request over a serial line. The script use simple python socket to listen 
for incoming modbus requests, and pyserial to repeat the request over serial line. 

mbs_client: Modbus TCP reader.
------------------------------
mbs_client.py -h
usage: mbs_client.py [-h] [-l TCP_PORT] [-i TCP_IP] [-n UNIT_NUMBER]
                     [-a ADRESS] [-c COUNT] [-t TIMEOUT] [-f] [-v VALUE]
                     [-r {3,4,16}]

Modbus TCP reader.

optional arguments:
  -h, --help      show this help message and exit
  -l TCP_PORT     ip port to use (default: 502)
  -i TCP_IP       ip of server unit
  -n UNIT_NUMBER  unit number
  -a ADRESS       register start adress (first adress is 1)
  -c COUNT        number of registers to read
  -t TIMEOUT      repeat readings evry N sec (modbus commands 3 and 4)
  -f              parse values as int (default is float)
  -v VALUE        value to write to register (modbus command 16)
  -r {3,4,16}     modbus command, 3: read holding registers, 4: read input
                  registers, 16: write input registers

mbs_server: Modbus TCP to Serial repeater.
------------------------------------------
mbs_server.py -h
usage: mbs_server.py [-h] [-l TCP_PORT] [-b BAUDRATE] [-p PARITY] [-c PORT]
                     [-t TAL] [-d]

Modbus TCP to Serial repeater.

optional arguments:
  -h, --help   show this help message and exit
  -l TCP_PORT  ip port to listen (default: 502)
  -b BAUDRATE  serial port baudrate (default: 38400)
  -p PARITY    serial port parity (default: E)
  -c PORT      serial port com-port
  -t TAL       serial port tal addr
  -d           print debug information
