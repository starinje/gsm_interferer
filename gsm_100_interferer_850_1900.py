#!/usr/bin/python

import socket, sys
import csv
import subprocess, os, glob
import re, os
import time
from optparse import OptionParser


#Define functions
#########################################################################################################################

 
def tcbin(x, y=32): 
   
    #This function returns the padded, two's complement representation of x, in y-bits.
    #It is conventional for y to be 8, 16, 32 or 64, though y can have any non-zero positive value. 
    
    if x >= (2**(y - 1)) or x < -(2**(y - 1) or y < 1):
        raise Exception("Argument outside of range.")
    if x >= 0:
        binstr = bin(x)
        # pad with leading zeros
        while len(binstr) < y + 2:
            binstr = "0b0" + binstr[2:]
        return binstr
    return bin((2**y) + x) # x is negative

#listen to response back
def send_command(command_list,sock):
	for command in command_list:
		sock.send(command)
		time.sleep(.05)
		
#scale to max amplitude of 16000
def scale_amplitude(amplitude_list):
	i = 0
	for amplitude in amplitude_list:
		if amplitude == 0:
			amplitude_list[i] = 1600
		elif amplitude_list[i] == 1:
			amplitude_list[i] = 3200
		elif amplitude_list[i] == 2:
			amplitude_list[i] = 4800
		elif amplitude_list[i] == 3:
			amplitude_list[i] = 6200
		elif amplitude_list[i] == 4:
			amplitude_list[i] = 7800
		elif amplitude_list[i] == 5:
			amplitude_list[i] = 9400
		elif amplitude_list[i] == 6:
			amplitude_list[i] = 11000
		elif amplitude_list[i] == 7:
			amplitude_list[i] = 12600
		elif amplitude_list[i] == 8:
			amplitude_list[i] = 14200
		elif amplitude_list[i] == 9:
			amplitude_list[i] = 15800
		i = i + 1
	return amplitude_list
	

def parse_file(config_file):

	
	file  = open(config_file, "rb")
	reader = csv.reader(file, delimiter=',')

	#store arfcn values and amplitudes into lists arfcn[] and amplitude[] and ip_address
	amplitude = []
	arfcn = []

	i = 0
	for row in reader:
		if i == 0:
			ip_address = row[0]
			i = 1
		else:
	    		arfcn.append(int(row[0]))
			amplitude.append(int(row[1]))
	
	#Convert arfcn values into lists of frequencies
	gsm_downlink_frequency_850 = []
	gsm_downlink_frequency_1900 = []
	amplitude_850 = []
	amplitude_1900 = []
	disable_indicator = 0
	counter_850 = 0
	counter_1900 = 0
	arfcn_850 = []
	arfcn_1900 = []
	error_flag = 0

	interferer_number = 0
	for numbers in arfcn:

			if arfcn[interferer_number] == 0: 
				disable_indicator = 1
			#GSM 850
			elif (arfcn[interferer_number] >= 128 and arfcn[interferer_number] <= 251): 
				downlink_freq = 869.2 + (0.2 * (arfcn[interferer_number] - 128))
				round(downlink_freq,3)
				gsm_downlink_frequency_850.append(1000000*downlink_freq)
				amplitude_850.append(amplitude[interferer_number])
				counter_850 += 1
				arfcn_850.append(str(arfcn[interferer_number]))
				
				

			#PCS-1900
			elif (arfcn[interferer_number] >= 512 and arfcn[interferer_number] <= 810): 
				downlink_freq = 1930.2 + (0.2 * (arfcn[interferer_number] - 512))
				round(downlink_freq,3)
				gsm_downlink_frequency_1900.append(1000000*downlink_freq)
				amplitude_1900.append(amplitude[interferer_number])
				counter_1900 += 1
				arfcn_1900.append(str(arfcn[interferer_number]))
		

			
			else:
				error_flag = 1

			interferer_number +=  1

	
	
	return gsm_downlink_frequency_850, gsm_downlink_frequency_1900, amplitude_850, amplitude_1900, ip_address, disable_indicator, arfcn_850, arfcn_1900, counter_850, counter_1900, error_flag


def interferer_freq_to_baseband(interferer_freq_list, local_oscillator, offset):
	i = 0
	for frequency in interferer_freq_list:
		interferer_freq_list[i] = (interferer_freq_list[i]-local_oscillator + offset)
		i = i + 1
	return interferer_freq_list


def open_socket(ip_address):
	port = 1028

	#Create socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	#Connect to server and check for errors
	try:
		sock.connect((ip_address,port))
	except socket.error, e:
		print "connection error: %s" % e
		sys.exit(1)
	except socket.gaierror, e:
		print "connection error: %s" % e
		sys.exit(1)
	except socket.herror, e:
		print "connection error: %s" % e
		sys.exit(1)
	except socket.timeout, e:
		print "connection error: %s" % e
		sys.exit(1)
	return sock


def init_comblocks():

	#Module: 4005 <- 2001 <- 1600 <- 5003 -> 1600 -> 2001 -> 4006
	#IDs:     006 <-  00? <-  002 <-  001 ->  003 ->  00? ->  007

	#Point of entry = COM-5003
	
	#ID 002 = COMBLOCK-1600 GSM 850
	#ID 003 = COMBLOCK-1600 PCS 1900

	#ID 006 = COMBLOCK-4005 GSM 850
	#ID 007 = COMBLOCK-4005 PCS 1900

	#Assign module ID's (Module Initialization)
	init_commands = ["@111SAC000\r\n",
			"@111MFW0\r\n",
			"@000SAC001\r\n",
			"@001GMI\r\n",
			"@001MFW2\r\n",
			"@000SAC002\r\n",
			"@002GMI\r\n",
			"@001MFW3\r\n",
			"@000SAC003\r\n",
			"@003GMI\r\n",
			"@001MFW4\r\n",
			"@000SAC003\r\n",
			"@003GMI\r\n",
			"@001MFW2\r\n",
			"@002MFW1\r\n",
			"@000SAC004\r\n",
			"@004GMI\r\n",
			"@002MFW2\r\n",
			"@000SAC004\r\n",
			"@004GMI\r\n",
			"@002MFW3\r\n",
			"@000SAC005\r\n",
			"@005GMI\r\n",
			"@001MFW4\r\n",
			"@003MFW1\r\n",
			"@000SAC005\r\n",
			"@005GMI\r\n",
			"@003MFW2\r\n",
			"@000SAC005\r\n",
			"@005GMI\r\n",
			"@003MFW3\r\n",
			"@000SAC006\r\n",
			"@006GMI\r\n",
			"@001MFW2\r\n",
			"@002MFW2\r\n",
			"@004MFW1\r\n",
			"@000SAC006\r\n",
			"@006GMI\r\n",
			"@004MFW2\r\n",
			"@000SAC006\r\n",
			"@006GMI\r\n",
			"@004MFW3\r\n",
			"@000SAC007\r\n",
			"@007GMI\r\n",
			"@001MFW4\r\n",
			"@003MFW2\r\n",
			"@005MFW1\r\n",
			"@000SAC007\r\n",
			"@007GMI\r\n",
			"@005MFW2\r\n",
			"@000SAC007\r\n",
			"@007GMI\r\n",
			"@005MFW3\r\n",
			"@000SAC008\r\n",
			"@008GMI\r\n",
			"@001MFW2\r\n",
			"@002MFW2\r\n",
			"@004MFW2\r\n",
			"@006MFW1\r\n",
			"@000SAC008\r\n",
			"@008GMI\r\n",
			"@006MFW2\r\n",
			"@000SAC008\r\n",
			"@008GMI\r\n",
			"@006MFW3\r\n",
			"@000SAC008\r\n",
			"@008GMI\r\n",
			"@001MFW4\r\n",
			"@003MFW2\r\n",
			"@005MFW2\r\n",
			"@007MFW1\r\n",
			"@000SAC008\r\n",
			"@008GMI\r\n",
			"@007MFW2\r\n",
			"@000SAC008\r\n",
			"@008GMI\r\n",
			"@007MFW3\r\n",
			"@000SAC008\r\n",
			"@008GMI\r\n",
			"@111MFW9\r\n",
			"@111MFW9\r\n",
			"@111MFW9\r\n",
			"@111MFW9\r\n",
			"@111MFW9\r\n",
			"@111MFW9\r\n",
			"@111MFW9\r\n"]

	return init_commands


def clear_register_commands(module_id):

	clear_commands = []
	clear_commands.append("@" + module_id + "SRG0000\r\n")
	clear_commands.append("@" + module_id + "SRG0100\r\n")
	clear_commands.append("@" + module_id + "SRG0200\r\n")
	clear_commands.append("@" + module_id + "SRG0300\r\n")
	clear_commands.append("@" + module_id + "SRG0400\r\n")
	clear_commands.append("@" + module_id + "SRG0500\r\n")
	clear_commands.append("@" + module_id + "SRG0600\r\n")
	clear_commands.append("@" + module_id + "SRG0700\r\n")
	clear_commands.append("@" + module_id + "SRG0800\r\n")
	clear_commands.append("@" + module_id + "SRG0900\r\n")

	i = 10
	while i <= 164:
		clear_commands.append("@" + module_id + "SRG" + str(i) + "00\r\n")
		i = i + 1

	clear_commands.append("@" + module_id + "SRG20000\r\n")
	return clear_commands


def configure_fpga(module_id, frequency_list, amplitude_list):

	fpga_commands = []

	command_set_iq_a = "@" + module_id + "SRG00FF\r\n"
	command_set_iq_b = "@" + module_id + "SRG017F\r\n"

	fpga_commands.append(command_set_iq_a)
	fpga_commands.append(command_set_iq_b)


	i = 0
	n = 0
	reg = []
	counter = 0

	fpga_clock_rate = 120E6

	for freq_value in frequency_list:
		interferer_freq = long((freq_value * pow(2,32))/fpga_clock_rate)
		interferer_freq = tcbin(interferer_freq)
		interferer_freq =  long(interferer_freq,2)
		amp = amplitude_list[counter]

		#Shifting 32-bit frequency value and masking. LSB ---> MSB
		reg_2 = interferer_freq >> 0  & 0x000000FF
		reg_3 = interferer_freq >> 8  & 0x000000FF
		reg_4 = interferer_freq >> 16 & 0x000000FF
		reg_5 = interferer_freq >> 24 & 0x000000FF
		
		#Shifting 16-bit amplitude value and masking
		reg_6 = amp >> 0 & 0x00FF
		reg_7 = amp >> 8 & 0x00FF
	
		reg_2 = str("%.2X" % reg_2)
		reg_3 = str("%.2X" % reg_3)
		reg_4 = str("%.2X" % reg_4)
		reg_5 = str("%.2X" % reg_5)
		reg_6 = str("%.2X" % reg_6)
		reg_7 = str("%.2X" % reg_7)

		commands = []
		commands.append(reg_2)
		commands.append(reg_3)
		commands.append(reg_4)
		commands.append(reg_5)
		commands.append(reg_6)
		commands.append(reg_7)
	
	
		if counter == 0:
			#Frequency
			fpga_commands.append("@" + module_id + "SRG02" + commands[0] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG03" + commands[1] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG04" + commands[2] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG05" + commands[3] + "\r\n")

			#Amplitude
			fpga_commands.append("@" + module_id + "SRG06" + commands[4] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG07" + commands[5] + "\r\n")


		elif counter == 1:
			#Frequency
			fpga_commands.append("@" + module_id + "SRG08" + commands[0] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG09" + commands[1] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG10" + commands[2] + "\r\n")

			fpga_commands.append("@" + module_id + "SRG11" + commands[3] + "\r\n")

			#Amplitude

			fpga_commands.append("@" + module_id + "SRG12" + commands[4] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG13" + commands[5] + "\r\n")


		else:

			#Frequency
			fpga_commands.append("@" + module_id + "SRG" + str(n+14) + commands[0] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG" + str(n+15) + commands[1] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG" + str(n+16) + commands[2] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG" + str(n+17) + commands[3] + "\r\n")

			#Amplitude

			fpga_commands.append("@" + module_id + "SRG" + str(n+18) + commands[4] + "\r\n")
			fpga_commands.append("@" + module_id + "SRG" + str(n+19) + commands[5] + "\r\n")
			n = n + 6
		
		counter = counter + 1

	
	#Enable Command
	command_enable = "@" + module_id + "SRG20000\r\n"
	fpga_commands.append(command_enable)

	return fpga_commands


def configure_quadrature_modulator(local_oscillator_frequency, module_id, gain):
	
	quadrature_modulator_commands = []

	#Shifting 32-bit frequency value and masking. LSB ---> MSB
	reg_0 = local_oscillator_frequency >> 0  & 0x000000FF
	reg_1 = local_oscillator_frequency >> 8  & 0x000000FF
	reg_2 = local_oscillator_frequency >> 16 & 0x000000FF
	reg_3 = local_oscillator_frequency >> 24 & 0x000000FF

	reg_4 = gain >> 0 & 0xFF
	reg_5 = gain >> 8 & 0x03
		
	reg_0 = str("%.2X" % reg_0)
	reg_1 = str("%.2X" % reg_1)
	reg_2 = str("%.2X" % reg_2)
	reg_3 = str("%.2X" % reg_3)

	reg_4 = str("%.2X" % reg_4)
	reg_5 = str("%.2X" % reg_5)
	
	commands = []
	commands.append(reg_0)
	commands.append(reg_1)
	commands.append(reg_2)
	commands.append(reg_3)
	
	quadrature_modulator_commands.append("@" + module_id + "SRG00" + commands[0] + "\r\n")
	quadrature_modulator_commands.append("@" + module_id + "SRG01" + commands[1] + "\r\n")
	quadrature_modulator_commands.append("@" + module_id + "SRG02" + commands[2] + "\r\n")
	quadrature_modulator_commands.append("@" + module_id + "SRG03" + commands[3] + "\r\n")

	#Register 6 (External Frequency Reference / Modulator On) 
	quadrature_modulator_commands.append("@" + module_id + "SRG0615\r\n")

	quadrature_modulator_commands.append("@" + module_id + "SRG04" + reg_4 + "\r\n")
	quadrature_modulator_commands.append("@" + module_id + "SRG05" + reg_5 + "\r\n")

	#Enable Command
	quadrature_modulator_commands.append("@" + module_id + "SRG3503\r\n")

	return quadrature_modulator_commands
	

def disable_quadrature_modulator(module_id):

	disable_quadrature_modulator_commands = []	

	disable_quadrature_modulator_commands.append("@" + module_id + "SRG0611\r\n")
	#Enable Command
	disable_quadrature_modulator_commands.append("@" + module_id + "SRG3503\r\n")
	
	return disable_quadrature_modulator_commands
	
#MAIN
#########################################################################################################################


#parse the command line
parser = OptionParser()
parser.add_option("-f", "--config_file", type="string", default=None, help=None)
(options, args) = parser.parse_args() 

#generate comblock initilization commands
init_commands_list = init_comblocks()

#define module ID's
fpga_850_module_id = "002"
fpga_1900_module_id = "003"

qm_850_module_id = "006"
qm_1900_module_id = "007"

#generate clear GSM-850 fpga register commands (comblock 1600)
clear_registers_fpga_850 = clear_register_commands(fpga_850_module_id)

#generate clear PCS-1900 fpga register commands (comblock 1600)
clear_registers_fpga_1900 = clear_register_commands(fpga_1900_module_id)

#parse file
print "Parsing Configuration File..."
time.sleep(1)
f_850,f_1900,a_850,a_1900, ip_address, disable_indicator, arfcn_850, arfcn_1900, counter_850, counter_1900, error_flag = parse_file(options.config_file)

if error_flag == 0:
	#create disable quadrature modulator commands
	disable_quadrature_modulator_850_commands = disable_quadrature_modulator(qm_850_module_id)
	disable_quadrature_modulator_1900_commands = disable_quadrature_modulator(qm_1900_module_id)

	#scale GSM_850 amplitude
	normalised_a_850 = scale_amplitude(a_850)

	#scale PCS_1900 amplitude
	normalised_a_1900 = scale_amplitude(a_1900)

	#define local oscillator frequency 
	lo_850 = 881700000
	lo_1900 = 1960000000

	#define frequency offset
	offset_850 = 0
	offset_1900 = 0

	#define quadrature modulator gain (0 - 1023)
	gain_850 = 100
	gain_1900 = 100
	
	#convert GSM-850 interferer frequencies to baseband frequencies and adjust for LO error
	adjusted_baseband_frequency_850 = interferer_freq_to_baseband(f_850, lo_850, offset_850)

	#convert PCS-1900 interferer frequencies to baseband frequencies and adjust for LO error
	adjusted_baseband_frequency_1900 = interferer_freq_to_baseband(f_1900, lo_1900, offset_1900)

	#configure GSM-850 fpga
	egsm_850_fpga_commands = configure_fpga(fpga_850_module_id, adjusted_baseband_frequency_850, normalised_a_850)

	#configure PCS-1900 fpga
	pcs_1900_fpga_commands = configure_fpga(fpga_1900_module_id, adjusted_baseband_frequency_1900, normalised_a_1900)

	#configure GSM-850 quadrature modulator
	egsm_850_qm_commands = configure_quadrature_modulator(lo_850, qm_850_module_id, gain_850)

	#configure PCS-1900 quadrature modulator
	pcs_1900_qm_commands = configure_quadrature_modulator(lo_1900, qm_1900_module_id, gain_1900)

	#open socket
	print "Establishing Connection with " + ip_address
	socket = open_socket(ip_address)
	time.sleep(1)
	print "Connection Established"
	time.sleep(1)
	print "Configuring Interferer Signals... \n"

	#disables or enables interferer
	if disable_indicator == 1:
		print "Interferer Disabled"
		#send disable commands
		send_command(init_commands_list,socket)
		send_command(clear_registers_fpga_850,socket)
		send_command(clear_registers_fpga_1900,socket)
		send_command(disable_quadrature_modulator_850_commands,socket)
		send_command(disable_quadrature_modulator_1900_commands,socket)
	else:
		#send enable commands
		send_command(init_commands_list,socket)
		send_command(clear_registers_fpga_850,socket)
		send_command(clear_registers_fpga_1900,socket)
		send_command(egsm_850_fpga_commands,socket)
		send_command(pcs_1900_fpga_commands,socket)
		send_command(egsm_850_qm_commands,socket)
		send_command(pcs_1900_qm_commands,socket)

	#close socket
	socket.close()

	if counter_850 > 0:
			print "Generating " + str(counter_850) + " GSM 850 Interferer Signals"
			time.sleep(.2)
			for numbers in arfcn_850:
				print "ARFCN: " + numbers
				time.sleep(.2)
	print "\n"
	if counter_1900 > 0:
			print "Generating " + str(counter_1900) + " PCS 1900 Interferer Signals"
			time.sleep(.2)
			for numbers in arfcn_1900:
				print "ARFCN: " + numbers
				time.sleep(.2)
			print "\n"

else:
	print "Configuration File Is Corrupt -- Check Syntax"