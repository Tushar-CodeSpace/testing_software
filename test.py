# given data
given_regex = r"^[A-Z0-9]{6,20}$"
given_scenarios = [{"DBAR": 0.1, "IBAR": 0.1, "DNFR": 0.1, "CFGR": 0.1, "SUCC": 0.6}]
given_machine_details= [
    {
    'machine_01':{
        'machine_key' : 'IBS001',
        'tcp_server_ip' : '127.0.0.1',
        'tcp_server_port' : '3001',
        'dm' : 'DM01'
        },
    'machine_02':{
        'machine_key' : 'IBS002',
        'tcp_server_ip' : '127.0.0.1',
        'tcp_server_port' : '3002',
        'dm' : 'DM02'
        }
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
    def noread(counter:int):
        return f'NoRead{counter}'

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



# main simulation
noread_counter = 0
tid_counter = 0
sid_counter = 0

machines = given_machine_details[0]

try:
    while True:
        scenario = getOneScenario(given_scenarios)

        tid_counter += 1
        sid_counter += 1

        if scenario == 'DBAR':
            noread_counter += 1
            code = barcode.noread(noread_counter)
        elif scenario == 'IBAR':
            code = barcode.invalid()
        else:
            code = barcode.valid()

        for machine_id, machine in machines.items():
            pb_string = pbFormatter(
                machine['machine_key'],
                tid_counter,
                machine['dm'],
                sid_counter,
                code=code
            )
            logger.info(f"[{machine_id}] PB string generated: {pb_string}")

        time.sleep(1)

except KeyboardInterrupt:
    logger.info("Simulation stopped by user")
