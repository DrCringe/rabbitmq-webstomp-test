import pika
import threading
from flask import Flask, Response
from flask_cors import CORS
from flask_restful import Resource, Api, reqparse


RMQ_HOST = '127.0.0.1'
RMQ_PORT = 5672
RMQ_VHOST = '/'
RMQ_EXCHANGE = 'testExchange'
RMQ_QUEUE = 'testRabbitWebStompQueue'
RMQ_RKEY = '1'
RMQ_MESSAGE_PUBLISH_INTERVAL = 5    # in seconds

BINDR_HOST = '127.0.0.1'
BINDR_PORT = 8888


message = ''
def set_message(new_message):
    global message
    message = new_message

def parse_commands(lock: threading.Lock, set_message):
    lock.acquire()
    msg = 'Hello world!'

    while (True):
        if (msg == 'exit'):
            print('Received exit command, shutting down...')
            lock.release()
            break
        elif (msg == ''):
            print('Message must not be empty, try again:')
        else:
            print(f'Serving a RabbitMQ topic sender, current message - "{msg}", enter new message to change:')
            set_message(msg)

        
        msg = input()


bindr = Flask(__name__)
cors = CORS(bindr, resources={r"/*": {"origins": "*"}})
api = Api(bindr)

class HandleBindingRequest(Resource):
    def post(self, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('queue', type=str)
        parser.add_argument('durable', type=bool)
        parser.add_argument('exclusive', type=bool)
        parser.add_argument('auto_delete', type=bool)
        parser.add_argument('routing_key', type=str)

        body = parser.parse_args()
        try:
            connection.add_callback_threadsafe(channel.queue_declare(body['queue'], False, body['durable'], body['exclusive'], body['auto_delete']))
            connection.add_callback_threadsafe(channel.queue_bind(body['queue'], RMQ_EXCHANGE, body['routing_key']))
        except TypeError:
            pass
        
        print('[ Bindr ] Created binding for queue %s to test exchange', body['queue'])

        return Response(status=200)

api.add_resource(HandleBindingRequest, '/bind')

queue_binder = threading.Thread(target=bindr.run, args=(BINDR_HOST, BINDR_PORT), daemon=True)
queue_binder.start()


lock = threading.Lock()
cli_prompt = threading.Thread(target=parse_commands, args=(lock, set_message), daemon=True)
cli_prompt.start()

credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters(RMQ_HOST, RMQ_PORT, RMQ_VHOST, credentials))
channel = connection.channel()

channel.exchange_declare(RMQ_EXCHANGE, 'topic')
while not (lock.acquire(True, RMQ_MESSAGE_PUBLISH_INTERVAL)):
    channel.basic_publish(RMQ_EXCHANGE, RMQ_RKEY, message)

connection.close()

lock.release()
cli_prompt.join()

