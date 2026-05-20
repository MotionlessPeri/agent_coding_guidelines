#!/usr/bin/env python3
"""
Direct TCP helper for UnrealMCP plugin.
Bypasses Claude Code MCP integration — sends JSON commands directly to UE Editor.

Usage:
    python ue_cmd.py <command> [json_params]

Examples:
    python ue_cmd.py ping
    python ue_cmd.py get_editor_state
    python ue_cmd.py save_and_exit_editor
    python ue_cmd.py get_actors_in_level
    python ue_cmd.py set_actor_property '{"actor_name":"MyActor","property_name":"Foo","property_value":"Bar"}'
"""

import socket
import json
import sys

HOST = "127.0.0.1"
PORT = 55557
TIMEOUT = 10
RECV_BUF = 1 << 20  # 1MB


def send_command(command: str, params: dict | None = None) -> dict:
    payload = {"type": command}
    if params:
        payload["params"] = params

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    try:
        sock.connect((HOST, PORT))
        sock.sendall(json.dumps(payload).encode("utf-8"))
        # Read until connection closed or timeout
        chunks = []
        while True:
            try:
                data = sock.recv(RECV_BUF)
                if not data:
                    break
                chunks.append(data)
                # Try to parse — if valid JSON, we're done
                try:
                    return json.loads(b"".join(chunks).decode("utf-8"))
                except json.JSONDecodeError:
                    continue
            except socket.timeout:
                break
        raw = b"".join(chunks).decode("utf-8")
        if raw:
            return json.loads(raw)
        return {"error": "No response received"}
    except ConnectionRefusedError:
        return {"error": f"Connection refused — is UE Editor running with UnrealMCP on {HOST}:{PORT}?"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        sock.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None

    result = send_command(command, params)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
