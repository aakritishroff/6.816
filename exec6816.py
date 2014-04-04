import subprocess
import os
import sys
import time

# queue: 'cqsub' or 'cqbigsub'
# command: the command you want to execute leaving spaces for the parameters
#  example: "java ParallelPacket 2000 [n] [w] false [trial] 8 [l] [s]
# params: dictionary from parameter identifier (like 'n') to list of choices
#  example: {'n': [1, 2, 8], 'w': [2000, 4000], 'trial': range(5), l: [0, 1], s: [0, 1, 2, 3]}
def exec6816(queue, command, params):

	param_list = [] # each parameter gets an index here containing the list of possible choices
	param_identifiers = [] # from param index in param_list to the parameter identifier

	for p_ident in params:
		param_identifiers.append(p_ident)
		param_list.append([str(p_choice) for p_choice in params[p_ident]]) # we only want to use strings

	qfile = exec6816_qinit()
	exec6816_qclear(qfile) # clear the execution queue
	exec6816_combinations(qfile, command, param_list, param_identifiers, 0) # try every combination of parameters
	exec6816_qrun(qfile, queue) # run the execution queue until its done
	exec6816_qclear(qfile) # clean up

# this goes through a param_list/param_identifiers combination and tries every combination
#  into the command string
def exec6816_combinations(qfile, command, param_list, param_identifiers, i):
	if i >= len(param_list):
		exec6816_qpush(qfile, command) # push a command to execution queue
		return

	for p_choice in param_list[i]: # each choice for current parameter
		command_choice = command.replace('[' + param_identifiers[i] + ']', p_choice) # set the parameter to the choice in command string
		exec6816_combinations(qfile, command_choice, param_list, param_identifiers, i + 1)

# below are the actual queue functions
# the way this works is, we first write every combination into some temporary file
# then we keep running jobs via queue until we get everything done in the file

# returns a temporary file path to use
def exec6816_qinit():
	return 'exec6816.q.txt'

# deletes the current current file path
def exec6816_qclear(qfile):
	try:
		os.remove(qfile)
	except:
		pass

# writes a command to execute to the qfile
def exec6816_qpush(qfile, command):
	fout = open(qfile, 'a')
	fout.write(command + "\n")
	fout.close()

# run the given queue file on the given queue
def exec6816_qrun(qfile, queue):
	while True: # loop until all of the commands are done
		fin = open(qfile, 'r')
		commands = [line for line in fin.readlines() if line.strip()]
		fin.close()

		if len(commands) == 0:
			break

		# run remaining commands
		subprocess.call([queue, 'python', 'exec6816.py', qfile])

# this is done when we try to run this guy
def exec6816_worker():
	qfile = sys.argv[1]
	fin = open(qfile, 'r')
	commands = [line.strip() for line in fin.readlines() if line.strip()]
	fin.close()

	while commands:
		command = commands.pop()
		p = subprocess.Popen(['bash', '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		lines = [line for line in out.split("\n") if line.strip()]

		for line in lines:
			fout = open(qfile + '.log', 'a')
			fout.write('[' + command + '] ' + line + "\n")
			fout.close()

		# update job file
		fout = open(qfile, 'w')
		fout.write("\n".join(commands))
		fout.close()

		# sleep so user can kill if it looks like there was problem
		time.sleep(5)

if __name__ == '__main__' and len(sys.argv) >= 2:
	exec6816_worker()
