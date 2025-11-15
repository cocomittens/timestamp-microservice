import zmq
import json

def handle_request(request):
    request_1 = {}
    request_json = json.dumps(request)
    socket.send_string(request_json)
    response_json = socket.recv_string()
    response = json.loads(response_json)
    return response


def handle_response(response):
    if response["valid"]:
        if "difference_ms" in response:
            print(f"Difference ms: {response["difference_ms"]}")
        if "timestamp" in response:
            print(f"Timestamp: {response["timestamp"]}")
        if "timezone" in response:
            print(f"Timezone: {response["timezone"]}")
    else:
        print(f"Validation error: {response['error']}")


context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5234")

request_1 = {}
request_2 = {"timestamps":["2025-11-12T10:00:00Z","2025-11-12T12:30:00+02:00"]}
request_3 = {"timestamps":[1731402000]}

response_1 = handle_request(request_1)
response_2 = handle_request(request_2)
response_3 = handle_request(request_3)

handle_response(response_1)
handle_response(response_2)
handle_response(response_3)
socket.close()
context.term()