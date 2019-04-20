#!/usr/bin/python3

import logging
FORMAT = '%(module)s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
from logging import debug,info,warn,critical,error

import sys
import optparse
import struct

I2C_HDR = '<LBBBBHH'
HDR_LEN = struct.calcsize(I2C_HDR)
ETYPES = { 0x09: '24C32', 0x0a: '24C64' }
DTYPES = { 0x01: 'Application' }
SIGNATURE = 0x04513200

P = optparse.OptionParser(usage='%prog [options]')

P.add_option('-d','--decode',dest='decode',action='store_true',
	help='decode i2c eeprom data, yield raw firmware',default=False)
P.add_option('-e','--encode',dest='encode',action='store_true',
	help='encode i2c eeprom data from raw firmware',default=False)

P.add_option('-o','--output',dest='output',action='store',
	metavar='FILENAME',help='Output file.',default=None)


opts,args = P.parse_args()
if not ( opts.encode ^ opts.decode ) :
	P.error('You have to specify either -e or -d (--encode or --decode).')

if len(args) == 0 :
	data = sys.stdin.read()
	info('%d bytes read from stdin.'%(len(data)))
else :
	data = open(args[0],'rb').read()
	info('%d bytes read from "%s".'%(len(data),args[0]))


if opts.decode :
	if len(data) < HDR_LEN :
		error('Cannot decode header: Less than %d bytes of input!'%(
			HDR_LEN))
		sys.exit(1)

	sign,hsiz,vers,etyp,dtyp,dsiz,chksum = \
			struct.unpack(I2C_HDR,data[0:HDR_LEN])

	info('Decoded header:')
	if sign == SIGNATURE :
		info('  Signature:   $%08x (ok)'%(sign))
	else :
		info('  Signature:   $%08x (NOT OK, expected $%08x)'%(
			sign,SIGNATURE))
	if hsiz == HDR_LEN :
		info('  Header Len.: $%02x (ok)'%(hsiz))
	else :
		info('  Header Len.: $%02x (NOT OK, expected $%02x)'%(
				hsiz,HDR_LEN))
	info('  Version:     $%02x'%(vers))
	info('  EEProm-Type: $%02x (%s)'%(etyp,ETYPES.get(etyp,'unknown')))
	info('  Data Type:   $%02x (%s)'%(dtyp,DTYPES.get(dtyp,'unknown')))
	info('  Data Size:   $%04x (dec: %d)'%(dsiz,dsiz))
	info('  Checksum:    $%04x'%(chksum))

	end_index = HDR_LEN + dsiz
	if len(data) < end_index :
		error('Not enough input, need at least %d bytes.'%(end_index))
		sys.exit(1)

	local_ck = sum(data[HDR_LEN:end_index]) & 0xffff
	info('Checksum calculated from image file:')

	if local_ck != chksum :
		warn('  Checksum:    $%04x (*!!WRONG!!*)'%(local_ck))
	else :
		info('  Checksum:    $%04x (ok)'%(local_ck))

	if opts.output :
		open(opts.output,'wb').write(data[HDR_LEN:end_index])
		info('Raw image written to file "%s".'%(opts.output))
	else :
		info('Raw image written to stdout.')
		sys.stdout.buffer.write(data[HDR_LEN:end_index])

	sys.exit(0)


if opts.encode :
	sign = SIGNATURE
	hsiz = HDR_LEN
	vers = 0
	etyp = 0x0a
	dtyp = 1
	dsiz = len(data)
	chksum = 0
	for b in data:
		intb=int( struct.unpack('B', b)[0] ) 
		#print(intb)
		chksum = chksum + intb
	chksum = chksum & 0xffff
	hdr = struct.pack(I2C_HDR,sign,hsiz,vers,etyp,dtyp,dsiz,chksum)

	outdata = hdr + data

	if opts.output :
		open(opts.output,'wb').write(outdata)
		info('Formatted image written to file "%s".'%(opts.output))
	else :
		info('Formatted image written to stdout.')
		sys.stdout.buffer.write(str(outdata))
