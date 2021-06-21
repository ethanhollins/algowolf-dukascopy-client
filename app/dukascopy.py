import numpy as np
import pandas as pd
import time
import os
import ntplib
import shortuuid
import subprocess
import requests
import json
import traceback
from . import tradelib as tl
from threading import Thread
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATEWAY_RUN_DIR = os.path.join(ROOT_DIR, 'JForex-3-SDK.jar')


class Subscription(object):

	def __init__(self, broker, msg_id):
		self.broker = broker
		self.msg_id = msg_id


	def onUpdate(self, *args):
		print(f'ON UPDATE: {args}', flush=True)

		self.broker._send_response(
			self.msg_id,
			{
				'args': list(args),
				'kwargs': {}
			}
		)


class Dukascopy(object):

	def __init__(self, sio, user_id, broker_id, username, password, is_demo):
		print('Dukascopy INIT', flush=True)

		self.sio = sio

		self.userId = user_id
		self.brokerId = broker_id
		self.username = username
		self.password = password
		self.isDemo = is_demo

		self.accounts = []
		self._is_gateway_connected = False		


	def _start_gateway(self):
		print(f'[_start_gateway] Dukascopy GATEWAY: {["java", "-jar", GATEWAY_RUN_DIR, self.userId, self.brokerId, self.username, self.password, str(self.isDemo).lower()]}', flush=True)

		if self.brokerId is None:
			brokerId = 'null'
		else:
			brokerId = self.brokerId

		self._gateway_process = subprocess.Popen(
			[ 
				'java', '-jar', GATEWAY_RUN_DIR, brokerId
			]
		)

		while not self._is_gateway_connected: pass

		return { 'complete': True }


	def onGatewayConnected(self):
		print('[onGatewayConnected] Connected!', flush=True)
		self._is_gateway_connected = True




