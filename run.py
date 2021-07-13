import sys
import socketio
import os
import json
import time
import traceback
from app.dukascopy import Dukascopy

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

'''
Utilities
'''
class UserContainer(object):

	def __init__(self, sio):
		self.sio = sio
		self.parent = None
		self.users = {}

	def setParent(self, parent):
		self.parent = parent


	def getParent(self):
		return self.parent


	def addUser(self, user_id, broker_id, username, password, is_demo, is_parent):
		if broker_id not in self.users:
			self.users[broker_id] = Dukascopy(self.sio, user_id, broker_id, username, password, is_demo)
			if is_parent:
				self.parent = self.users[broker_id]

		return self.users[broker_id]


	def deleteUser(self, port):
		if broker_id in self.users:
			self.users[broker_id].stop()
			del self.users[broker_id]


	def getUser(self, broker_id):
		return self.users.get(broker_id)


	def findUser(self, user_id, broker_id):
		for broker_id in self.users:
			user = self.users[broker_id]
			if (
				user.userId == user_id and
				user.brokerId == broker_id
			):
				return True

		return -1


def getConfig():
	path = os.path.join(ROOT_DIR, 'instance/config.json')
	if os.path.exists(path):
		with open(path, 'r') as f:
			return json.load(f)
	else:
		raise Exception('Config file does not exist.')


'''
Initialize
'''

config = getConfig()
sio = socketio.Client(reconnection=False)
user_container = UserContainer(sio)

'''
Socket IO functions
'''

def sendResponse(msg_id, res):
	res = {
		'msg_id': msg_id,
		'result': res
	}

	sio.emit(
		'broker_res', 
		res, 
		namespace='/broker'
	)


def onAddUser(user_id, broker_id, username, password, is_demo, is_parent):
	print(f'[onAddUser] {broker_id}, {user_container.users}', flush=True)
	if not broker_id in user_container.users:
		print(f'[onAddUser] 1', flush=True)
		user = user_container.addUser(user_id, broker_id, username, password, is_demo, is_parent)
		user._start_gateway()
	print(f'[onAddUser] 2', flush=True)	
	return {
		'complete': True
	}


def onDeleteUser(port):
	user_container.deleteUser(port)

	return {
		'completed': True
	}


def onReplaceUser(port, user_id, strategy_id, broker_id):
	user_container.replaceUser(port, user_id, strategy_id, broker_id)

	return {
		'completed': True
	}


def onFindUser(user_id, strategy_id, broker_id):
	port = user_container.findUser(user_id, strategy_id, broker_id)

	return {
		'port': port
	}


def getExistingUsers():
	for port in user_container.users:
		pass


def getUser(port):
	return user_container.getUser(port)


def getParent():
	return user_container.getParent()


def findUnusedPort(used_ports):
	print(f'[findUnusedPort] {used_ports}', flush=True)

	max_port = 5000
	for port in user_container.users:
		if port != str(5000):
			if int(port) > max_port:
				max_port = int(port)
			if not port in used_ports:
				if not user_container.users[port].isLoggedIn().get('result'):
					print(f'[findUnusedPort] {port}', flush=True)
					return { 'result': port }

	print(f'[findUnusedPort] {max_port+1}', flush=True)

	return { 'result': max_port+1 }


# Download Historical Data EPT
def _download_historical_data_broker( 
	user, product, period, tz='Europe/London', 
	start=None, end=None, count=None,
	include_current=True,
	**kwargs
):
	return user._download_historical_data_broker(
		product, period, tz='Europe/London', 
		start=start, end=end, count=count,
		**kwargs
	)


def _subscribe_chart_updates(user, msg_id, instrument):
	user._subscribe_chart_updates(msg_id, instrument)
	return {
		'completed': True
	}


# Create Position EPT

# Modify Position EPT

# Delete Position EPT

# Create Order EPT

# Modify Order EPT

# Delete Order EPT

# Get Account Details EPT

# Get All Accounts EPT

def reconnect():
	while True:
		try:
			sio.connect(
				config['STREAM_URL'], 
				headers={
					'Broker': 'ib'
				}, 
				namespaces=['/broker']
			)
			break
		except Exception:
			pass
	print('RECONNECTED!', flush=True)


@sio.on('connect', namespace='/broker')
def onConnect():
	print('CONNECTED!', flush=True)


@sio.on('disconnect', namespace='/broker')
def onDisconnect():
	print('DISCONNECTED', flush=True)
	reconnect()


@sio.on('broker_cmd', namespace='/broker')
def onCommand(data):
	print(f'COMMAND: {data}', flush=True)

	try:
		cmd = data.get('cmd')
		broker = data.get('broker')
		broker_id = data.get('broker_id')

		if broker_id is None:
			user = getParent()
		else:
			user = getUser(broker_id)

		if broker == 'dukascopy':
			res = {}
			if cmd == 'add_user':
				res = onAddUser(*data.get('args'), **data.get('kwargs'))

			elif cmd == 'user_exists':
				pass

			elif cmd == 'gateway_connected':
				user.onGatewayConnected()

			if len(res):
				sendResponse(data.get('msg_id'), res)

	except Exception as e:
		print(traceback.format_exc(), flush=True)
		sendResponse(data.get('msg_id'), {
			'error': str(e)
		})


def createApp():
	print('CREATING APP')
	while True:
		try:
			sio.connect(
				config['STREAM_URL'], 
				headers={
					'Broker': 'dukascopy'
				}, 
				namespaces=['/broker']
			)
			break
		except Exception:
			pass

	return sio


if __name__ == '__main__':
	sio = createApp()
	print('DONE')
