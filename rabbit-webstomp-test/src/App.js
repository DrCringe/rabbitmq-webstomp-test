import './App.css';
import { useEffect, useState } from 'react';
import { ActivationState, Client } from '@stomp/stompjs';

const SOCKET_URL = 'ws://127.0.0.1:15674/ws';
const TEST_QUEUE_NAME = 'testRabbitWebStompQueue';

function App() {
  const [subscription, setSubscription] = useState(null);
  const [client, setClient] = useState(new Client({
    brokerURL: SOCKET_URL,
    connectHeaders: {
      login: 'guest',
      passcode: 'guest',
    },
    onStompError: (error) => {
      console.error('STOMP error: ', error);
    },
    onWebSocketError: (error) => {
      console.error('WebSocket error: ', error);
    },
    debug: function (str) {
      console.debug(str);
    },
    reconnectDelay: 0,
  }));

  const activateRabbitMQwsClient = () => {
    if (client.state === ActivationState.ACTIVE) return;
    else if (client.state !== ActivationState.DEACTIVATING) client.activate();
    setTimeout(activateRabbitMQwsClient, 100);
  }

  useEffect(() => {
    client.onConnect = () => console.debug('Successfully opened websocket connection');
    client.onDisconnect = () => console.debug('Disconnected from WebSocket client');
    client.onStompError = (e) => console.error('Websocket connection error:', e);
    activateRabbitMQwsClient();

    return () => {
      client.deactivate()
      .then(() => console.debug('Successfully closed websocket connection'))
      .catch(err => console.error(err));
    }
  }, []);

  const testSubscribe = () => {
    if (client.connected) {
      setSubscription(
        client.subscribe(`/queue/${TEST_QUEUE_NAME}`, (message) => {
          if (message.body) {
            console.log('[ - TEST - ] Received websocket message:', message.body);
          }
        }, {
          durable: 'false',
          'auto-delete': 'true',
          exclusive: 'false'
        })
      );
      requestBinding();
    } else {
      console.error('[ - TEST - ] RabbitMQ websocket client is not connected');
    }
  }

  const requestBinding = () => {
    fetch('http://127.0.0.1:8888/bind', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          queue: TEST_QUEUE_NAME,
          durable: false,
          auto_delete: true,
          exclusive: false,
          routing_key: '1'
      })
    })
    .then(response => {
      if (~~(response.status / 100) === 2) {
        console.debug("Binding request successful");
      } else {
        console.error("Binding request failed with status code " + response.status);
      }
    })
    .catch(err => console.error(err));
  }

  const testUnsubscribe = () => subscription && subscription.unsubscribe();

  return (
    <div className="App">
      <header className="App-header">
        {/* <img src={logo} className="App-logo" alt="logo" /> */}
        <p className="App-text">
          Nothing here, check debug console)
        </p>
        <div className="Flex-row">
          <button className="App-button App-text" onClick={testSubscribe}>Subscribe</button>
          <button className="App-button App-text" onClick={testUnsubscribe}>Unsubscribe</button>
        </div>
      </header>
    </div>
  );
}

export default App;
