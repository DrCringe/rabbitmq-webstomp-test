import threading
import pika
import requests
from pika.adapters.blocking_connection import BlockingChannel


RMQ_HOST = '127.0.0.1'
RMQ_PORT = 5672
RMQ_VHOST = '/'
RMQ_QUEUE = 'testRabbitWebStompQueue'
RMQ_RKEY = '1'

BINDR_HOST = '127.0.0.1'
BINDR_PORT = 8888


def parse_commands(consume_lock: threading.Lock, exit_lock: threading.Lock):
    print('RabbitMQ auto-delete queue test. Enter "start" to declare queue and begin consuming messages')
    consume_lock.acquire()
    exit_lock.acquire()

    while (True):
        command = input()

        if (command == 'exit'):
            print('Received exit command, shutting down...')
            break
        elif (command == 'stop'):
            if (len(channel.consumer_tags) == 0):
                print('No consumers are active right now')
            else:
                connection.add_callback_threadsafe(stop_consuming_callback)
        elif (command == 'start'):
            if (consume_lock.locked()):
                consume_lock.release()
            else:
                print('Message receiving is already in progress')
        elif (command == 'bind'):
            print('Requesting queue binding from server...')
            request_binding()
        elif (command == 'help' or command == 'usage'):
            print('Available commands:\n\tstart\t\t- begin comsuming RabbitMQ messages')
            print('\tstop\t\t- stop consuming RabbitMQ messages (should delete "auto-delete" queue)')
            print('\tbind\t\t- request binding for test queue to test exchange from server')
            print('\texit\t\t- stop consuming messages and exit the program')
            print('\thelp | usage\t- print this help')
        elif (command == ''):
            print('Command must not be empty, try again:')
        else:
            print(f'Unknown command - "{command}", try again:')
        print()
    
    exit_lock.release()
    if consume_lock.locked: consume_lock.release()
    connection.add_callback_threadsafe(stop_consuming_callback)

def callback(ch, method, properties, body):
    print('Message received: key="%r", body="%r"' % (method.routing_key, body))

def stop_consuming_callback():
    channel.stop_consuming()

def request_binding():
    try:
        response = requests.post('http://localhost:8888/bind', json={
            'queue': RMQ_QUEUE,
            'durable': False,
            'exclusive': False,
            'auto_delete': True,
            'routing_key': RMQ_RKEY
        })
        if response.status_code == 200:
            print('Binding request successful')
        else:
            print('Binding request failed with status code %d', response.status_code)
    except requests.ConnectionError:
        print('Failed to connect to binding server')

credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters(RMQ_HOST, RMQ_PORT, RMQ_VHOST, credentials))
channel = connection.channel()

consume_lock = threading.Lock()
exit_lock = threading.Lock()
cli_prompt = threading.Thread(target=parse_commands, args=(consume_lock, exit_lock), daemon=True)

cli_prompt.start()

while (consume_lock.acquire(blocking=True)):
    if (exit_lock.acquire(blocking=False)):
        print('[ Consumer ] Shutting down consumer thread...')
        break

    print('[ Consumer ] Declaring RabbitMQ queue...')
    channel.queue_declare(RMQ_QUEUE, auto_delete=True, durable=False)

    print('[ Consumer ] Receiving messages')
    channel.basic_consume(RMQ_QUEUE, callback, auto_ack=False)
    channel.start_consuming()

    print('[ Consumer ] Stopped receiving messages')


connection.close()
cli_prompt.join()
