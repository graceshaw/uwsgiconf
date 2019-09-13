import pickle
from functools import partial

from .. import uwsgi
from ..utils import decode

__offloaded_functions = {}


def _mule_messages_hook(message):
    # Processes mule messages, tries to decode it.
    try:
        loaded = pickle.loads(message)

    except Exception:  # py3 pickle.UnpicklingError
        return

    else:
        if not isinstance(loaded, tuple):
            return

        return __offloaded_functions[loaded[1]](*loaded[2], **loaded[3])


uwsgi.mule_msg_hook = _mule_messages_hook


def __offload(func_name, mule_or_farm, *args, **kwargs):
    # Sends a message to a mule/farm, instructing it
    # to run a function using given arguments,
    Mule(mule_or_farm).send(pickle.dumps(
        (
            'uwcf',
            func_name,
            args,
            kwargs,
        )
    ))


def mule_offload(mule_or_farm=None):
    """Decorator. Use to offload function execution to a mule or a farm.

    :param int|str|Mule|Farm mule_or_farm:

    """
    if isinstance(mule_or_farm, Mule):
        mule_or_farm = mule_or_farm.id
    elif isinstance(mule_or_farm, Farm):
        mule_or_farm = mule_or_farm.name

    mule_or_farm = mule_or_farm or 0

    def mule_offload_(func):
        func_name = func.__name__
        __offloaded_functions[func_name] = func
        return partial(__offload, func_name, mule_or_farm)
        
    return mule_offload_


class Mule(object):
    """Represents uWSGI Mule."""

    __slots__ = ['id']

    def __init__(self, id):
        """
        :param int id: Mule ID

        """
        self.id = id

    def offload(self):
        """Decorator. Allows to offload function execution on this mule."""
        return mule_offload(self)

    @classmethod
    def get_current_id(cls):
        """Returns current mule ID. Returns 0 if not a mule.

        :rtype: int
        """
        return uwsgi.mule_id()

    @classmethod
    def get_current(cls):
        """Returns current mule object or None if not a mule.

        :rtype: Optional[Mule]
        """
        mule_id = cls.get_current_id()

        if not mule_id:
            return None

        return Mule(mule_id)

    @classmethod
    def get_message(cls, signals=True, farms=False, buffer_size=65536, timeout=-1):
        """Block until a mule message is received and return it.

        This can be called from multiple threads in the same programmed mule.

        :param bool signals: Whether to manage signals.

        :param bool farms: Whether to manage farms.

        :param int buffer_size:

        :param int timeout: Seconds.

        :rtype: str|unicode

        :raises ValueError: If not in a mule.
        """
        return decode(uwsgi.mule_get_msg(signals, farms, buffer_size, timeout))

    def send(self, message):
        """Sends a message to a mule(s)/farm.

        :param str|unicode message:

        :rtype: bool

        :raises ValueError: If no mules, or mule ID or farm name is not recognized.
        """
        return uwsgi.mule_msg(message, self.id)


class Farm(object):
    """Represents uWSGI Mule Farm."""

    __slots__ = ['name']

    def __init__(self, name):
        """
        :param str|unicode name: Mule farm name.

        """
        self.name = name

    def offload(self):
        """Decorator. Allows to offload function execution on mules of this farm."""
        return mule_offload(self)

    @property
    def is_mine(self):
        """Returns flag indicating whether current mule belongs
        to this farm.

        :param str|unicode name: Farm name.

        :rtype: bool
        """
        return uwsgi.in_farm(self.name)

    @classmethod
    def get_message(cls):
        """Reads a mule farm message.

         * http://uwsgi.readthedocs.io/en/latest/Embed.html

         .. warning:: Bytes are returned for Python 3.

         :rtype: str|unicode|None

         :raises ValueError: If not in a mule
         """
        return decode(uwsgi.farm_get_msg())

    def send(self, message):
        """Sends a message to the given farm.

        :param str|unicode message:

        """
        return uwsgi.farm_msg(self.name, message)
