from enum import Enum


class AppStatus(str, Enum):
    Starting = 'starting'
    Failing = 'failing'
    Running = 'running'
