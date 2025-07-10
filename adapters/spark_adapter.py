import json
import time
import websocket
from urllib.parse import urlencode
from urllib.parse import urlparse

class Adapter:
    def __init__(self, config):
        self.config = config
        self.proxy = None
        if proxy := config.get('proxy'):
            parsed = urlparse(proxy)
            self.proxy = {
                "host": parsed.hostname,
                "port": parsed.port or (80 if parsed.scheme == "http" else 443)
            }

    def create_chat_completion(self, data):
        ws_url = self._build_ws_url()
        ws_options = {}
        if self.proxy:
            ws_options = {
                "http_proxy_host": self.proxy["host"],
                "http_proxy_port": self.proxy["port"]
            }
            
        ws = websocket.create_connection(ws_url, **ws_options)
        
        request = {
            "header": {"app_id": self.config['app_id']},
            "parameter": {"chat": {"domain": "generalv3"}},
            "payload": {"message": {"text": history + [{"role": "user", "content": query}]}}
        }
        
        ws.send(json.dumps(request))
        result = ''
        while True:
            response = json.loads(ws.recv())
            if response['header']['code'] != 0:
                raise RuntimeError(f"Spark error: {response['header']}")
            result += response['payload']['choices']['text'][0]['content']
            if response['header']['status'] == 2:
                break
        ws.close()
        
        return {
            "id": f"spark-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": data['model'],
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": result},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0}
        }
    
    def _build_ws_url(self):
        params = {
            "appid": self.config['app_id'],
            "timestamp": str(int(time.time())),
        }
        return f"wss://spark-api.xf-yun.com/v3.1/chat?{urlencode(params)}"