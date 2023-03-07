from enum import IntEnum


class ControllerStatus(IntEnum):
    waiting_for_payload = 1
    controller_sending = 2
    connector_sent = 3
