from collections import OrderedDict
from .utils import listify


if False:  # pragma: nocover
    from .config import Section


class Options(object):
    """Options descriptor. Allows option."""

    def __init__(self, opt_type):
        """
        :param opt_type:
        """
        self.opt_type = opt_type

    def __get__(self, section, section_cls):
        """

        :param Section section:
        :param OptionsGroup options_obj:
        :rtype: OptionsGroup
        """
        key = self.opt_type.__name__

        try:
            options_obj = section._options_objects.get(key)

        except AttributeError:
            # Allow easy access to option group static params:
            # Section.networking.socket_types.DEFAULT
            return self.opt_type

        if not options_obj:
            options_obj = self.opt_type(_section=section)

        section._options_objects[key] = options_obj

        return options_obj


class OptionKey(object):

    __slots__ = ['key']

    def __init__(self, key):
        self.key = key

    def swap(self, new_key):

        if new_key:
            self.key = '%s' % new_key

    def __str__(self):
        return self.key


class OptionsGroup(object):
    """Introduces group of options.

    Basic group parameters may be passed to initializer
    or `set_basic_params` method.

    Usually methods setting parameters are named `set_***_params`.

    Methods ending with `_params` return section object and may be chained.

    """
    _section = None  # type: Section
    """Section this option group belongs to."""

    plugin = False  # type: bool|str|unicode
    """Indication this option group belongs to a plugin."""

    name = None
    """Name to represent the group."""

    def __init__(self, *args, **kwargs):
        if self._section is None:
            self._section = kwargs.pop('_section', None)  # type: Section

        self.set_basic_params(*args, **kwargs)

    def _get_name(self, *args, **kwargs):
        """
        :rtype: str
        """
        return self.name

    def __str__(self):
        return self._get_name()

    def __call__(self, *args, **kwargs):
        """The call is translated into ``set_basic_params``` call.

        This approach is much more convenient yet IDE most probably won't
        give you a hint on what arguments are accepted.

        :param args:
        :param kwargs:
        :rtype: Section
        """
        return self.set_basic_params(*args, **kwargs)

    def set_basic_params(self, *args, **kwargs):
        """
        :rtype: Section
        """
        return self._section

    def _set(self, key, value, condition=True, cast=None, multi=False, plugin=None, priority=None):
        """

        :param str|unicode key: Option name

        :param value: Option value. Can be a lis if ``multi``.

        :param condition: Condition to test whether this option should be added to section.
            * True - test value is not None.

        :param cast: Value type caster.
            * bool - treat value as a flag

        :param bool multi: Indicate that many options can use the same name.

        :param str|unicode plugin: Plugin this option exposed by. Activated automatically.

        :param int priority: Option priority indicator. Options with lower numbers will come first.

        """
        key = OptionKey(key)

        def set_plugin(plugin):
            self._section.set_plugins_params(plugins=plugin)

        def handle_priority(value, use_list=False):

            if priority is not None:
                # Restructure options.
                opts_copy = opts.copy()
                opts.clear()

                existing_value = opts_copy.pop(key, [])

                if use_list:
                    existing_value.extend(value)
                    value = existing_value

                for pos, (item_key, item_val) in enumerate(opts_copy.items()):

                    if priority == pos:
                        opts[key] = value

                    opts[item_key] = item_val

                return True

        def handle_plugin_required(val):

            if isinstance(val, ParametrizedValue):
                key.swap(val.opt_key or key)

                if val.plugin:
                    # Automatic plugin activation.
                    set_plugin(val.plugin)

                if val._opts:
                    opts.update(val._opts)

        if condition is True:
            condition = value is not None

        if condition is None or condition:

            opts = self._section._opts

            if cast is bool:
                if value:
                    value = 'true'

                else:
                    try:
                        del opts[key]
                    except KeyError:
                        pass

                    return

            if self.plugin is True:
                # Automatic plugin activation when option from it is used.
                set_plugin(self)

            if plugin:
                set_plugin(plugin)

            if isinstance(value, tuple):  # Tuple - expect ParametrizedValue.
                list(map(handle_plugin_required, value))
                value = ' '.join(map(str, value))

            if multi:
                values = []

                # First activate plugin if required.
                for value in listify(value):
                    handle_plugin_required(value)
                    values.append(value)

                # Second: list in new option.
                if not handle_priority(values, use_list=True):
                    opts.setdefault(key, []).extend(values)

            else:
                handle_plugin_required(value)

                if not handle_priority(value):
                    opts[key] = value


class ParametrizedValue(OptionsGroup):
    """Represents parametrized option value."""

    alias = None
    """Alias to address this value."""

    args_joiner = ' '
    """Symbol to join arguments with."""

    name_separator = ':'
    """Separator to add after name portion."""

    name_separator_strip = False
    """Strip leading and trailing name separator from the result."""

    opt_key = None
    """Allows swapping default uption key with custom value"""

    def __init__(self, *args):
        self.args = args
        self._opts = OrderedDict()
        super(ParametrizedValue, self).__init__(_section=self)

    def __str__(self):
        args = [str(arg) for arg in self.args if arg is not None]

        result = ''

        if not self.opt_key:
            result += self._get_name() + self.name_separator

        result += self.args_joiner.join(args)

        if self.alias:
            result = '%s %s' % (self.alias, result)

        result = result.strip()

        if self.name_separator_strip:
            result = result.strip(self.name_separator)

        return result
