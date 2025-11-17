import os
import socket
import threading
import queue
import time
import iris
import pytest
from pathlib import Path

IN_HOST = os.getenv("SERVICE_IN_HOST", "127.0.0.1")
IN_PORT = int(os.getenv("SERVICE_IN_PORT", "12345"))
OUT_HOST = os.getenv("SERVICE_OUT_HOST", "127.0.0.1")
OUT_PORT = int(os.getenv("SERVICE_OUT_PORT", "12346"))
MESSAGE  = os.getenv("SERVICE_TEST_MESSAGE", "sending message via my service\n")


def wait_for_port(host: str, port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError as e:
            last_err = e
            time.sleep(0.2)
    raise TimeoutError(f"Port {host}:{port} not ready within {timeout}s (last error: {last_err})")


def start_listener(host: str, port: int, recv_q: queue.Queue) -> threading.Thread:
    """Start a background TCP listener that publishes first non-empty payload to recv_q."""
    ready = threading.Event()

    def _listener():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(5)
        ready.set()  # signal that bind/listen are complete

        deadline = time.time() + 20  # overall time we'll wait for data
        payload = b""
        try:
            while time.time() < deadline and not payload:
                # accept one connection at a time until we actually get bytes
                srv.settimeout(max(0.1, deadline - time.time()))
                try:
                    conn, _addr = srv.accept()
                except socket.timeout:
                    continue
                with conn:
                    conn.settimeout(5)
                    chunks = []
                    while True:
                        try:
                            data = conn.recv(4096)
                        except socket.timeout:
                            break
                        if not data:
                            break
                        chunks.append(data)
                        # stop early if newline seen (typical for echo)
                        if b"\n" in data:
                            break
                    if chunks:
                        payload = b"".join(chunks)
                        break
        finally:
            srv.close()
            recv_q.put(payload)  # b"" if nothing arrived

    t = threading.Thread(target=_listener, daemon=True)
    t.start()
    assert ready.wait(3), "Listener failed to start within 3s"
    return t


def _detect_repo_root() -> Path:
    # Prefer GH Actions env when present
    ws = os.environ.get("GITHUB_WORKSPACE")
    if ws:
        return Path(ws).resolve()
    # Otherwise walk up from this file until we find a repo marker
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    return Path.cwd()


@pytest.fixture(scope="module",autouse=True)
def startprod():
    repo_root = _detect_repo_root()
    cls_host = repo_root / "tests" / "helpers" / "OsPyMixed" / "TCPAdaptersFromOs" / "Production.cls"
    if not cls_host.exists():
        raise FileNotFoundError(f"IRIS class file not found: {cls_host}")

    #nothing
    status = iris._SYSTEM.OBJ.Load(str(cls_host), "ck")
    print("production loading status = ", status)
    status = iris.Ens.Director.StartProduction("TCPAdaptersFromOs.Production")
    print("production starting status = ", status)
    end_loop = 1
    start_time = time.time()
    prod = iris.ref()
    running = iris.ref()
    while end_loop:
        if time.time()-start_time > 12:
            end_loop = 0
            print("unable to start production in 12 seconds")
            isrunning = 0
            break
        status = iris.Ens.Director.GetProductionStatus(prod, running)
        if running.value == 1:
            isrunning = 1
            end_loop = 0
        else:
            time.sleep(0.5)
    print("productionrunning status = ", isrunning)


    yield

    status = iris.Ens.Director.StopProduction()

    end_loop = 1
    start_time = time.time()
    prod = iris.ref()
    running = iris.ref()
    while end_loop:
        if time.time()-start_time > 12:
            end_loop = 0
            print("unable to stop production in 12 seconds")
        status = iris.Ens.Director.GetProductionStatus(prod, running)
        if running.value != 1:
            end_loop = 0
        else:
            time.sleep(0.5)
    



def test_service_relays_message():
    recv_q: queue.Queue[bytes] = queue.Queue()

    # 1) start the sink/listener on OUT_PORT (no probing via a connection!)
    listener_thread = start_listener(OUT_HOST, OUT_PORT, recv_q)

    # 2) wait for the service’s input side to be up
    wait_for_port(IN_HOST, IN_PORT, timeout=30)

    # 3) send the message to the service’s input port
    msg = MESSAGE if MESSAGE.endswith("\n") else MESSAGE + "\n"
    with socket.create_connection((IN_HOST, IN_PORT), timeout=5) as s:
        s.sendall(msg.encode("utf-8"))
        try:
            s.shutdown(socket.SHUT_WR)  # mimic nc -N / EOF
        except OSError:
            pass

    # 4) collect what the listener saw on OUT_PORT
    received = recv_q.get(timeout=25)
    rec_text = received.decode("utf-8", errors="ignore")

    # 5) assert
    expected = MESSAGE.strip()
    assert expected in rec_text, (
        f"Expected to receive substring {expected!r} on {OUT_HOST}:{OUT_PORT}, "
        f"but got {rec_text!r}"
    )

    listener_thread.join(timeout=1)
