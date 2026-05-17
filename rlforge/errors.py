"""Exception hierarchy for RLForge."""


class RLForgeError(Exception):
    """Base exception."""


class EnvError(RLForgeError):
    """Environment errors."""


class EnvResetError(EnvError): pass
class EnvStepError(EnvError): pass
class VectorEnvError(EnvError): pass


class BufferError(RLForgeError):
    """Buffer errors."""


class BufferEmptyError(BufferError): pass
class BufferFullError(BufferError): pass


class NetworkError(RLForgeError): pass
class NetworkInitError(NetworkError): pass
class DeviceError(NetworkError): pass


class ConfigError(RLForgeError): pass
