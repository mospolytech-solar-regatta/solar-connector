class SerialReadError(Exception):
    """Вызывается при ошибках чтения serial порта"""
    pass

class SerialWriteError(Exception):
    """Вызывается при ошибках записи serial порта"""
    pass
