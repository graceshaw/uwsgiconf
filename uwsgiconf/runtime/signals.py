from collections import namedtuple

from .. import uwsgi
from ..exceptions import UwsgiconfException
from ..utils import get_logger

_LOG = get_logger(__name__)


registry_signals = []  # type: list[SignalDescription]
"""Registered signals."""

SignalDescription = namedtuple('SignalDescription', ['num', 'target', 'func'])
"""Registered signal information."""


def get_available_num():
    """Returns first available signal number.

    :rtype: int

    :raises UwsgiconfException: If no signal is available.

    """
    for signum in range(0, 256):
        if not uwsgi.signal_registered(signum):
            return signum

    raise UwsgiconfException('No uWSGI signals available.')


def get_last_received():
    """Get the last signal received.

    :rtype: Signal
    """
    return Signal(uwsgi.signal_received())


class Signal(object):
    """Represents uWSGI signal.

    .. warning:: If you define a new function in worker1 and register
        it as a signal handler, only worker1 can run it. The best way to register signals
        is defining them in the master (.runtime.uwsgi.postfork_hooks.add), so all workers see them.

    .. code-block:: python

        signal = Signal()

        @signal.register_handler()
        def somefunc():
            pass

        # or the same:

        @signal
        def somefunc():
            pass

    """
    __slots__ = ['num']

    def __init__(self, num=None):
        """
        :param int num: Signal number (0-255).

            .. note:: If not set it will be chosen automatically.

        """
        self.num = num or get_available_num()

    def __int__(self):
        return self.num

    def __call__(self, func):
        # Allows using object as a decorator.
        return self.register_handler()(func)

    @property
    def registered(self):
        """Whether the signal is registered.

        :rtype: bool
        """
        return uwsgi.signal_registered(self.num)

    def register_handler(self, target=None):
        """Decorator for a function to be used as a signal handler.

        .. code-block:: python

            signal = Signal()

            @signal.register_handler()
            def somefunc():
                pass

        :param str target: Where this signal will be delivered to. Default: ``worker``.

            * ``workers``  - run the signal handler on all the workers
            * ``workerN`` - run the signal handler only on worker N
            * ``worker``/``worker0`` - run the signal handler on the first available worker
            * ``active-workers`` - run the signal handlers on all the active [non-cheaped] workers

            * ``mules`` - run the signal handler on all of the mules
            * ``muleN`` - run the signal handler on mule N
            * ``mule``/``mule0`` - run the signal handler on the first available mule

            * ``spooler`` - run the signal on the first available spooler
            * ``farmN/farm_XXX``  - run the signal handler in the mule farm N or named XXX

            * http://uwsgi.readthedocs.io/en/latest/Signals.html#signals-targets

        """
        target = target or 'worker'
        sign_num = self.num

        def wrapper(func):

            _LOG.debug(f"Registering '{func.__name__}' as signal '{sign_num}' handler ...")

            uwsgi.register_signal(sign_num, target, func)
            registry_signals.append(SignalDescription(sign_num, target, func))

            return func

        return wrapper

    def send(self, remote=None):
        """Sends the signal to master or remote.

        When you send a signal, it is copied into the master's queue.
        The master will then check the signal table and dispatch the messages.

        :param str|None remote: Remote address.

        :rtype: None

        :raises ValueError: If remote rejected the signal.

        :raises IOError: If unable to deliver to remote.
        """
        uwsgi.signal(self.num, *([remote] if remote is not None else []))

    def wait(self):
        """Waits for the given of any signal.

        Block the process/thread/async core until a signal is received. Use signal_received to get the number of
        the signal received. If a registered handler handles a signal, signal_wait will be interrupted and the actual
        handler will handle the signal.

        * http://uwsgi-docs.readthedocs.io/en/latest/Signals.html#signal-wait-and-signal-received

        :raises SystemError: If something went wrong.
        """
        uwsgi.signal_wait(self.num)


def _automate_signal(target, func):

    if target is None or isinstance(target, str):
        sig = Signal()

        func(sig)

        return sig.register_handler(target=target)

    func(target)
