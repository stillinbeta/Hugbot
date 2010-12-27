import socket 
import re
import sqlite3

HOST = 'irc.freenode.net'
PORT = 6667
NICK = 'HugBot2000'
REALNAME = 'Hugbot ZXOSULTRA v2'
OWNER='stillinbeta'
CHANNELINIT = '##hugbotsandbox'
ENCODING='UTF8'
ACTIONS = ('hugs')
DATABASE = 'hugbot.sqlite'

def ssend(self, string,encoding=ENCODING):
	print(string)
	return self.send(bytes(string+'\r\n',encoding))
def srecv(self,bufsize,encoding=ENCODING):
	return str(self.recv(bufsize),encoding)
socket.socket.ssend = ssend
socket.socket.srecv = srecv

msg_re = re.compile('^:(?P<username>\w+)!.+PRIVMSG (?P<channel>#\S+) :(?P<message>.+)')
alphanum_re = re.compile('[\W]+')
sql_update = "insert or replace into `hugs` values ('{0}','{1}','{2}', coalesce ( (select `count` from `hugs` where `giver` = '{0}' AND `action` = '{1}' AND `reciever` = '{2}'), 0) + 1 );"

max_sql = "select {0} from hugs where action = '{1}' group by {0} order by sum(count) desc limit 1";
max_sql_giver = max_sql.format('giver','{0}')
max_sql_reciever = max_sql.format('reciever','{0}')

conn = sqlite3.connect(DATABASE)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS hugs ( reciever, action, giver, count );")
c.execute("CREATE UNIQUE INDEX IF NOT EXISTS hugs_index ON hugs ( reciever, action, giver );")

s = socket.socket()
s.connect((HOST,PORT))

auth = False
join = False

def parse_line(line):
	matches = msg_re.match(line)
	if matches == None:
		print("Error Parsing String!"+line)
		return
	matches = matches.groupdict()

	if matches['message'].find('ACTION',1,7) is not -1: #There's a \0x01 before ACTION
		message = matches['message'].split(' ')
		if len(message) > 2:
			if (message[1] in ACTIONS):
				message[1] = alphanum_re.sub('',message[1])
				message[2] = alphanum_re.sub('',message[2])
				c.execute(sql_update.format(matches['username'],message[1],message[2]))
				conn.commit()
				print("{} {} {}".format(matches['username'],message[1],message[2]))
		return
	len_to = len(NICK + ': !')
	if matches['message'].find(NICK + ': !',0) is not -1:
		message = matches['message'][len_to:].split(' ')

		s.ssend("PRIVMSG {} :{}".format(matches['channel'],run_command(message)))

def run_command(message):
	print(message)
	cmd = alphanum_re.sub('',message[0])
	if cmd == "hugstats":
		try: 
			max_giver = c.execute(max_sql_giver.format('hugs')).fetchone()[0]
			max_reciever = c.execute(max_sql_reciever.format('hugs')).fetchone()[0]
		except Exception:
			return "Not enough hugs yet!"
		return "{} got the most hugs, {} gave the most, but everyone wins!".format(max_reciever, max_giver)
	else: 	
		return "ummmm... I don't know how to do that"	

try:
	while 1:
		line = s.srecv(512)
		
		if not auth and line.find("Checking Ident") is not -1:
			s.ssend('USER '+NICK+' * *:'+REALNAME)
			s.ssend('NICK '+NICK)
			auth = True
		elif not join and line.find(NICK+' :+i') is not -1:
			s.ssend('JOIN '+CHANNELINIT)
			join = True

		elif line.find("PING") is 0:
			line = line.split(' ')
			s.ssend("PONG "+line[1])
		elif join and auth:
			parse_line(line)
except KeyboardInterrupt:
	c.close()
	s.ssend("QUIT :buhbye!")
	exit()	
