from ..config import Section as _Section


class Section(_Section):
    """Basic nice configuration."""

    def __init__(self, name=None, touch_reload=None, workers=None, threads=None, **kwargs):
        """

        :param str|unicode name: Section name.

        :param str|list touch_reload: Reload uWSGI if the specified file or directory is modified/touched.

        :param int workers: Spawn the specified number of workers (processes).
            Default: workers number equals to CPU count.

        :param int threads: Number of threads per worker.

        :param kwargs:
        """
        super(Section, self).__init__(strict_config=True, name=name, **kwargs)

        if touch_reload:
            self.main_process.set_basic_params(touch_reload=touch_reload)

        if workers:
            self.workers.set_basic_params(count=workers)
        else:
            self.workers.set_count_auto()

        self.workers.set_thread_params(per_worker=threads)
        self.main_process.set_basic_params(vacuum=True)
        self.main_process.set_naming_params(autonaming=True)
        self.master_process.set_basic_params(enabled=True)
        self.locks.set_basic_params(thunder_lock=True)


class PythonSection(Section):
    """Basic nice configuration using Python plugin."""

    def __init__(self, name=None, basic_params_python=None, wsgi_module=None, **kwargs):
        """

        :param str|unicode name: Section name.

        :param dict basic_params_python: See PythonPlugin params

        :param str|unicode wsgi_module: wsgi application module path or filepath

            Example:
                mypackage.my_wsgi_module -- read from `application` attr of mypackage/my_wsgi_module.py
                mypackage.my_wsgi_module:my_app -- read from `my_app` attr of mypackage/my_wsgi_module.py

        :param kwargs:
        """
        super(PythonSection, self).__init__(
            name=name, basic_params_plugin_python=basic_params_python, **kwargs)

        plugin = self.plugin_python
        plugin.activate()

        if wsgi_module:
            plugin.set_wsgi_params(module=wsgi_module)
