
from helpers.entity import Entity
from helpers.entity_runner import EntityRunner
import http.client
import json
import ssl
import traceback


REQUEST_HEADERS = { 'Content-Type': 'application/json' }

REQUEST_WALLET_BALANCE_URL = '/get_wallet_balance'
REQUEST_WALLET_SYNCED_URL = '/get_sync_status'




class ChiaWalletSensor(Entity):

    def __init__(self, e_id: str, runner: EntityRunner, *, certificate_file: str = None, certificate_key: str = None, host: str = None, port: int = None, wallet_id: int = 1, mqtt_topic: str = None ):
        super().__init__(e_id, "chia_wallet", mqtt_topic)

        self.__runner: EntityRunner = runner

        self.__ssl_context: ssl.SSLContext = None
        self.__certificate_file: str = certificate_file
        self.__certificate_key: str = certificate_key

        self.__host: str = host
        self.__port: int = port

        self.__wallet_id: int = wallet_id


    def __create_ssl_context(self):
        self.__ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        self.__ssl_context.load_cert_chain(certfile=self.__certificate_file , keyfile=self.__certificate_key)

    def __get_wallet_info(self, wallet_id: int):

        try:
            request_body_dict = { 'wallet_id': wallet_id }

            connection = http.client.HTTPSConnection(self.__host, port=self.__port, context=self.__ssl_context)
            connection.request(method="POST", url=REQUEST_WALLET_BALANCE_URL, headers=REQUEST_HEADERS, body=json.dumps(request_body_dict))

            response = connection.getresponse()
            

            return json.loads(response.read())
            
        except:
            print(traceback.format_exc())

        return None

    def __get_wallet_synced(self):

        try:
            request_body_dict = {}

            connection = http.client.HTTPSConnection(self.__host, port=self.__port, context=self.__ssl_context)
            connection.request(method="POST", url=REQUEST_WALLET_SYNCED_URL, headers=REQUEST_HEADERS, body=json.dumps(request_body_dict))

            response = connection.getresponse()
            

            return json.loads(response.read())
        except:
            print(traceback.format_exc())

        return None


    async def setup(self):
        await self.__runner.get_loop_handler().schedule_work(self.__create_ssl_context)


    async def update(self):
        response = {}

        wallet_id = self.__wallet_id
        response['wallet_balance_{}'.format(wallet_id)] = (await self.__runner.get_loop_handler().schedule_work(self.__get_wallet_info, wallet_id))['wallet_balance']
        response['wallet_sync_status'] = await self.__runner.get_loop_handler().schedule_work(self.__get_wallet_synced)

        return response
