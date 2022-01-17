import stomp
import requests
from stomp.listener import PrintingListener, WaitingListener


RMQ_HOST = '127.0.0.1'
RMQ_WS_PORT = 61613
RMQ_QUEUE = 'testRabbitWebStompQueue'
RMQ_RKEY = '1'

def request_binding():
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

con = stomp.Connection([(RMQ_HOST, RMQ_WS_PORT)])
con.set_listener('pl', PrintingListener())
con.connect('guest', 'guest', True)

subscribed = False
sub_id = 1

print('RabbitMQ STOMP auto-delete queue test. Enter "subscribe" to suscribe to queue')
while (True):
    command = input()

    if (command == 'exit'):
        if subscribed:
            con.unsubscribe(sub_id)
        print('Received exit command, shutting down...')
        break
    elif (command == 'subscribe'):
        if subscribed:
            print('Already subscribed to test queue')
        else:
            con.subscribe(f'/queue/{RMQ_QUEUE}', sub_id, headers={'durable': 'false', 'exclusive': 'false', 'auto-delete': 'true'})
            # Using this headers leads to same result:   headers={'durable': 'true', 'exclusive': 'false', 'auto-delete': 'false', 'x-expires': '5000'}
            subscribed = True
    elif (command == 'unsubscribe'):
        if subscribed:
            con.unsubscribe(sub_id)
            subscribed = False
            sub_id += 1
        else:
            print('Not subscribed yet')
    elif (command == 'bind'):
        print('Requesting queue binding from server...')
        request_binding()
    elif (command == 'help' or command == 'usage'):
        print('Available commands:\n\tsubscribe\t- subscribe to test queue')
        print('\tunsubscribe\t- unsubscribe from test queue (should delete "auto-delete" queue)')
        print('\tbind\t\t- request binding for test queue to test exchange from server')
        print('\texit\t\t- unsubscribe if subscribed and exit the program')
        print('\thelp | usage\t- print this help')
    elif (command == ''):
        print('Command must not be empty, try again:')
    else:
        print(f'Unknown command - "{command}", try again:')