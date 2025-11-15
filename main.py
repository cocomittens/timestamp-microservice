import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import zmq


def get_current_timestamp(timezone_name=None):
    tz = timezone.utc if not timezone_name else ZoneInfo(timezone_name)
    return int(datetime.now(tz).timestamp())

def _parse_timestamp(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("Timestamp cannot be empty")
        sign = 1
        if text[0] == "-":
            sign = -1
            text_body = text[1:]
        else:
            text_body = text
        if text_body.isdigit():
            num = int(text_body) * sign
            if len(text_body) > 10:
                return datetime.fromtimestamp(num / 1000, timezone.utc)
            return datetime.fromtimestamp(num, timezone.utc)
        iso_text = text[:-1] + "+00:00" if text.endswith("Z") else text
        dt = datetime.fromisoformat(iso_text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    raise ValueError("Invalid timestamp value")

def get_timestamp_difference(timestamp_1, timestamp_2=None):
    first = _parse_timestamp(timestamp_1)
    second = datetime.now(timezone.utc) if timestamp_2 is None else _parse_timestamp(timestamp_2)
    delta = second - first if second >= first else first - second
    return int(delta.total_seconds() * 1000)

def main():
    """
    Main service loop
    Sets up ZeroMQ socket and listens for validation requests
    """
    # create zeromq context and socket
    context = zmq.Context()
    socket = context.socket(zmq.REP)

    port = 5234
    socket.bind(f"tcp://*:{port}")

    print("=" * 50)
    print("Timestamp Microservice")
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

                if "timestamps" in request:
                    timestamps = request["timestamps"]
                    if not isinstance(timestamps, list):
                        raise ValueError("Timestamps must be a list")
                    if not 1 <= len(timestamps) <= 2:
                        raise ValueError("Provide one or two timestamps")
                    difference = get_timestamp_difference(timestamps[0], timestamps[1] if len(timestamps) == 2 else None)
                    response = {
                        "valid": True,
                        "difference_ms": difference
                    }
                else:
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
