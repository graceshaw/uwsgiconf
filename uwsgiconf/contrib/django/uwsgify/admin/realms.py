from collections import OrderedDict
from datetime import datetime, timedelta

from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from .base import OnePageAdmin


class SummaryAdmin(OnePageAdmin):

    def contribute_onepage_context(self, request, context):
        from uwsgiconf.runtime.platform import uwsgi
        from uwsgiconf.runtime.logging import get_current_log_size
        from uwsgiconf.runtime.rpc import get_rpc_list
        from uwsgiconf.runtime.signals import get_available_num

        time_started = datetime.fromtimestamp(uwsgi.started_on)
        rss, vsz = uwsgi.memory

        info_basic = OrderedDict([
            (_('Version'), uwsgi.get_version()),
            (_('Hostname'), uwsgi.hostname),
            (_('Serving since'), time_started),
            (_('Serving for'), datetime.now() - time_started),
            (_('Clock'), uwsgi.clock),
            (_('Master PID'), uwsgi.master_pid),
            (_('Memory (RSS, VSZ)'), ', '.join((filesizeformat(rss), filesizeformat(vsz)))),
            (_('Buffer size'), uwsgi.buffer_size),
            (_('Cores'), uwsgi.cores_count),
            (_('Workers'), uwsgi.workers_count),
            (_('Threads support'), '+' if uwsgi.threads_enabled else '-'),
            (_('Current worker'), uwsgi.worker_id),
            (_('Requests by worker'), uwsgi.request.id),
            (_('Requests total'), uwsgi.request.total_count),
            (_('Socket queue size'), uwsgi.get_listen_queue()),
            (_('Log size'), get_current_log_size()),
            (_('RPC'), ', '.join(get_rpc_list())),
            (_('Available signal number'), get_available_num()),
        ])

        context.update({
            'panels': {
                '': {
                    'rows': OrderedDict(((key, [val]) for key, val in info_basic.items())),
                }
            },
        })


class ConfigurationAdmin(OnePageAdmin):

    def contribute_onepage_context(self, request, context):
        from uwsgiconf.runtime.platform import uwsgi

        context.update({
            'panels': {
                '': {'rows': OrderedDict(((key, [val]) for key, val in uwsgi.config.items()))},
            },
        })


class WorkersAdmin(OnePageAdmin):

    def contribute_onepage_context(self, request, context):
        from uwsgiconf.runtime.platform import uwsgi

        fromts = datetime.fromtimestamp

        info_worker_map = OrderedDict([
            ('id', (_('ID'), None)),
            ('pid', (_('PID'), None)),
            ('status', (_('Status'), None)),

            ('running_time', (_('Running for'), lambda val: timedelta(microseconds=val))),
            ('last_spawn', (_('Spawned at'), lambda val: fromts(val))),

            ('respawn_count', (_('Respawns'), None)),
            ('requests', (_('Requests'), None)),
            ('delta_requests', (_('Delta requests'), None)),  # Used alongside with MAX_REQUESTS
            ('exceptions', (_('Exceptions'), None)),
            ('signals', (_('Signals'), None)),

            ('rss', (_('RSS'), lambda val: filesizeformat(val))),
            ('vsz', (_('VSZ'), lambda val: filesizeformat(val))),

            ('tx', (_('Transmitted'), lambda val: filesizeformat(val))),
            ('avg_rt', (_('Avg. response'), lambda val: timedelta(microseconds=val))),

            # todo maybe
            # ('apps', (_(''), None)),
            # {
            #     'modifier1': 0,
            #     'chdir': '',
            #     'startup_time': 0,
            #     'callable': 139896737453968,
            #     'mountpoint': '',
            #     'exceptions': 0L,
            #     'interpreter': 19550368,
            #     'requests': 1L,
            #     'id': 0
            # },
        ])

        info_workers = OrderedDict()
        unknown = object()

        for info_worker in uwsgi.workers_info:
            for keyname, (name, func) in info_worker_map.items():

                value = info_worker.get(keyname, unknown)
                if value is unknown:
                    continue

                if func is not None:
                    value = func(value)

                info_workers.setdefault(name, []).append(value)

        context.update({
            'panels': {
                '': {'rows': info_workers},
            },
        })
