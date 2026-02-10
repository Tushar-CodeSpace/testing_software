# =========================
# GIVEN DATA
# =========================

given_regex = r"^[A-Z0-9]{6,20}$"

given_scenarios = [{"DBAR": 0.1, "IBAR": 0.1, "DNFR": 0.1, "CFGR": 0.1, "SUCC": 0.6}]

given_machine_details = [
    {
        "machine_01": {
            "machine_key": "IBS001",
            "tcp_server_ip": "127.0.0.1",
            "tcp_server_port": "3001",
            "dm": "DM01",
        },
        "machine_02": {
            "machine_key": "IBS002",
            "tcp_server_ip": "127.0.0.1",
            "tcp_server_port": "3002",
            "dm": "DM02",
        },
        "machine_03": {
            "machine_key": "IBS101",
            "tcp_server_ip": "127.0.0.1",
            "tcp_server_port": "3003",
            "dm": "DM03",
        },
        "machine_04": {
            "machine_key": "IBS102",
            "tcp_server_ip": "127.0.0.1",
            "tcp_server_port": "3004",
            "dm": "DM04",
        },
        "machine_05": {
            "machine_key": "IBS201",
            "tcp_server_ip": "127.0.0.1",
            "tcp_server_port": "3005",
            "dm": "DM05",
        },
        "machine_06": {
            "machine_key": "IBS301",
            "tcp_server_ip": "127.0.0.1",
            "tcp_server_port": "3006",
            "dm": "DM06",
        },
        "machine_07": {
            "machine_key": "IBS401",
            "tcp_server_ip": "127.0.0.1",
            "tcp_server_port": "3007",
            "dm": "DM07",
        },
    }
]

# =========================
# IMPORTS
# =========================

import random
import string
import re
import time
import socket
import threading
from colorama import Fore, Style, init

init(autoreset=True)

# =========================
# LOGGER (ONLY TAG COLORED)
# =========================

import threading
from datetime import datetime
from colorama import Fore, Style


class logger:
    _lock = threading.Lock()

    @staticmethod
    def _print(tag_color, tag, msg):
        now = datetime.now().strftime("%H:%M:%S")
        with logger._lock:
            print(
                f"{Fore.CYAN}{now}{Style.RESET_ALL} "
                f"{tag_color}{Style.BRIGHT}[{tag:<5}]{Style.RESET_ALL} {msg}",
                flush=True,
            )

    @staticmethod
    def info(msg):
        logger._print(Fore.GREEN, "INFO", msg)

    @staticmethod
    def warn(msg):
        logger._print(Fore.YELLOW, "WARN", msg)

    @staticmethod
    def error(msg):
        logger._print(Fore.RED, "ERROR", msg)


# =========================
# SCENARIO PICKER
# =========================


def getOneScenario(scenarios):
    scenario_dict = scenarios[0]
    names = list(scenario_dict.keys())
    probs = list(scenario_dict.values())
    return random.choices(names, probs, k=1)[0]


# =========================
# BARCODE GENERATOR
# =========================


class barcode:
    PATTERN = re.compile(given_regex)
    CHARS = string.ascii_uppercase + string.digits
    INVALID_CHARS = string.ascii_lowercase + "!@#$%^&*"

    @staticmethod
    def noread(counter):
        return f"NoRead{counter}"

    @classmethod
    def valid(cls):
        length = random.randint(6, 20)
        return "".join(random.choice(cls.CHARS) for _ in range(length))

    @classmethod
    def invalid(cls):
        mode = random.choice(["short", "long", "badchar"])

        if mode == "short":
            return "".join(
                random.choice(cls.CHARS) for _ in range(random.randint(1, 5))
            )

        elif mode == "long":
            return "".join(
                random.choice(cls.CHARS) for _ in range(random.randint(21, 30))
            )

        else:
            length = random.randint(6, 20)
            code = "".join(
                random.choice(cls.CHARS + cls.INVALID_CHARS) for _ in range(length)
            )
            if cls.PATTERN.match(code):
                return code.lower()
            return code


# =========================
# PB FORMATTER
# =========================


def pbFormatter(machine_key, tid, dm, mode, sid, code):
    return f"{machine_key},{tid},PB,{dm},{mode},{sid},{code}\n"


# =========================
# TCP CLIENT
# =========================


class TCPClient:
    def __init__(self, host, port, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.running = False

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            self.running = True
            logger.info(f"Connected → {self.host}:{self.port}")
            threading.Thread(target=self._receive_loop, daemon=True).start()
        except Exception as e:
            logger.error(f"Connect failed {self.host}:{self.port} → {e}")

    def _receive_loop(self):
        buffer = ""

        while self.running:
            try:
                data = self.sock.recv(1024)  # type: ignore
                if not data:
                    break

                chunk = data.decode(errors="ignore")
                buffer += chunk

                # Case 1: newline framed messages
                if "\n" in buffer:
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            logger.warn(f"{self.host}:{self.port} ← {line}")

                # Case 2: no newline (raw PLC packet)
                elif buffer:
                    logger.warn(f"{self.host}:{self.port} ← {buffer.strip()}")
                    buffer = ""

            except Exception as e:
                logger.error(f"RX error {self.host}:{self.port} → {e}")
                break

        self.close()

    def send(self, data):
        try:
            if self.sock:
                self.sock.sendall(data.encode())
                logger.info(f"{self.host}:{self.port} → {data.strip()}")
        except Exception as e:
            logger.error(f"Send failed → {e}")
            self.close()

    def close(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        logger.warn(f"Closed → {self.host}:{self.port}")


# =========================
# MAIN
# =========================

machines = given_machine_details[0]

clients = {}
for m in machines.values():
    c = TCPClient(m["tcp_server_ip"], int(m["tcp_server_port"]))
    c.connect()
    clients[m["machine_key"]] = c

noread_counter = 0
tid_counter = 0
sid_counter = {m["machine_key"]: 0 for m in machines.values()}

try:
    while True:
        scenario = getOneScenario(given_scenarios)
        logger.info(f"Scenario picked: {scenario}")
        tid_counter += 1

        for machine in machines.values():

            sid_counter[machine["machine_key"]] += 1

            if scenario == "DBAR":
                noread_counter += 1
                code = barcode.noread(noread_counter)
            elif scenario == "IBAR":
                code = barcode.invalid()
            else:
                code = barcode.valid()

            pb_string = pbFormatter(
                machine_key=machine["machine_key"],
                tid=tid_counter,
                dm=machine["dm"],
                mode="A",
                sid=sid_counter[machine["machine_key"]],
                code=code,
            )

            clients[machine["machine_key"]].send(pb_string)

        time.sleep(1)

except KeyboardInterrupt:
    logger.warn("Simulation stopped")

finally:
    for c in clients.values():
        c.close()
