# given data
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

# imports
import random
import string
import re
import time
from colorama import Fore, Style, init


# logger
class logger:
    init()

    @staticmethod
    def info(message: str):
        print(Fore.GREEN + Style.BRIGHT + " [INFO] " + Style.RESET_ALL + message)

    @staticmethod
    def error(message: str):
        print(Fore.RED + Style.BRIGHT + " [ERROR] " + Style.RESET_ALL + message)

    @staticmethod
    def warn(message: str):
        print(Fore.YELLOW + Style.BRIGHT + " [WARN] " + Style.RESET_ALL + message)


# choose one scenario
def getOneScenario(scenarios: list):
    logger.info("Choosing one of the given scenarios...")
    scenario_dict = scenarios[0]
    scenarios_name_list = list(scenario_dict.keys())
    scenarios_prob_list = list(scenario_dict.values())
    chosen_scenario = random.choices(
        population=scenarios_name_list, weights=scenarios_prob_list, k=1
    )[0]
    logger.info(f"Scenario picked: {chosen_scenario}")
    return chosen_scenario


# getOneScenario(given_scenarios)


# barcode generator
class barcode:
    PATTERN = re.compile(given_regex)

    CHARS = string.ascii_uppercase + string.digits
    INVALID_CHARS = string.ascii_lowercase + "!@#$%^&*"

    @staticmethod
    def noread(counter: int):
        return f"NoRead{counter}"

    @classmethod
    def valid(cls, min_len=6, max_len=20):
        length = random.randint(min_len, max_len)
        code = "".join(random.choice(cls.CHARS) for _ in range(length))
        return code

    @classmethod
    def invalid(cls):
        mode = random.choice(["short", "long", "badchar"])

        if mode == "short":
            length = random.randint(1, 5)  # less than 6
            return "".join(random.choice(cls.CHARS) for _ in range(length))

        elif mode == "long":
            length = random.randint(21, 30)  # more than 20
            return "".join(random.choice(cls.CHARS) for _ in range(length))

        else:  # badchar
            length = random.randint(6, 20)
            chars = cls.CHARS + cls.INVALID_CHARS
            code = "".join(random.choice(chars) for _ in range(length))

            # ensure it really breaks regex
            if cls.PATTERN.match(code):
                return code.lower()  # force invalid
            return code


# pb formatter -> <machine_key>,<TID>,PB,<dm>,<mode>,<SID>,<barcode>
def pbFormatter(machine_key: str, tid: int, dm: str, sid: int, code: str):
    pb_string = f"{machine_key},{tid},PB,{dm},{sid},{code}"
    return pb_string


# tcp client
import socket
import threading


class TCPClient:
    def __init__(self, host: str, port: int, timeout: int = 5):
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
            print(f"[CONNECTED] {self.host}:{self.port}")

            # Start receiver thread
            threading.Thread(target=self._receive_loop, daemon=True).start()

        except Exception as e:
            print(f"[ERROR] Connect failed: {e}")

    def send(self, data: str):
        try:
            if self.sock:
                self.sock.sendall(data.encode())
                print(f"[SENT] {data}")
        except Exception as e:
            print(f"[ERROR] Send failed: {e}")
            self.close()

    # Close connection
    def close(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        print("[CLOSED]")


# main simulation
noread_counter = 0
tid_counter = 0
sid_counter = 0

machines = given_machine_details[0]

try:
    client = TCPClient("127.0.0.1", 3001)
    client.connect()

    while True:
        scenario = getOneScenario(given_scenarios)

        tid_counter += 1
        sid_counter += 1

        if scenario == "DBAR":
            noread_counter += 1
            code = barcode.noread(noread_counter)
        elif scenario == "IBAR":
            code = barcode.invalid()
        else:
            code = barcode.valid()

        for machine_id, machine in machines.items():
            pb_string = pbFormatter(
                machine["machine_key"],
                tid_counter,
                machine["dm"],
                sid_counter,
                code=code,
            )
            logger.info(f"[{machine_id}] PB string generated: {pb_string}")

        time.sleep(1)

except KeyboardInterrupt:
    logger.info("Simulation stopped by user")
