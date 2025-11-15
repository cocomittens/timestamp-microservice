import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import zmq


def get_current_timestamp(timezone_name=None):
    tz = timezone.utc if not timezone_name else ZoneInfo(timezone_name)
    return int(datetime.now(tz).timestamp())

def get_timestamp_difference(timestamp_1, timestamp_2):
    pass

def main():
    """
    Main service loop
    Sets up ZeroMQ socket and listens for validation requests
    """
    # create zeromq context and socket
    context = zmq.Context()
    socket = context.socket(zmq.REP)

    port = 5444
    socket.bind(f"tcp://*:{port}")

    print("=" * 50)
    print("Randomizer Microservice")
    print("=" * 50)
    print(f"Status: Running")
    print(f"Port: {port}")
    print(f"Waiting for requests...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    print()

    request_count = 0


    try:
        while True:
            # wait for request from client
            message = socket.recv_string()
            request_count += 1

            print(f"[Request #{request_count}] Received: {message}")

            try:
                # parse JSON request
                request = json.loads(message)

                timezone_name = request.get("timezone")
                if timezone_name is None or timezone_name == "":
                    timezone_name = None
                elif not isinstance(timezone_name, str):
                    raise ValueError("Timezone must be a string")

                timestamp = get_current_timestamp(timezone_name)
                response = {
                    "valid": True,
                    "timestamp": timestamp,
                    "timezone": timezone_name or "UTC"
                }

                response_json = json.dumps(response)
                socket.send_string(response_json)

                print(f"[Request #{request_count}] Sent: {response_json}")
                print()

            except json.JSONDecodeError as e:
                # handle invalid JSON
                error_response = {
                    "valid": False,
                    "error": f"Invalid JSON: {str(e)}"
                }
                socket.send_string(json.dumps(error_response))
                print(f"[Request #{request_count}] Error: Invalid JSON")
                print()

            except (ZoneInfoNotFoundError, ValueError) as e:
                error_response = {
                    "valid": False,
                    "error": str(e)
                }
                socket.send_string(json.dumps(error_response))
                print(f"[Request #{request_count}] Error: {str(e)}")
                print()

            except Exception as e:
                # handle other errors
                error_response = {
                    "valid": False,
                    "error": f"Server error: {str(e)}"
                }
                socket.send_string(json.dumps(error_response))
                print(f"[Request #{request_count}] Error: {str(e)}")
                print()

    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("Shutting down Timestamp service...")
        print(f"Total requests processed: {request_count}")
        print("=" * 50)

    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    main()
