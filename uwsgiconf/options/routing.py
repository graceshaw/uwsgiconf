import os

from .routing_actions import *
from .routing_modifiers import *
from .routing_routers import *
from .routing_subjects import *
from .routing_vars import *
from ..base import OptionsGroup
from ..exceptions import ConfigurationError
from ..utils import listify, string_types


class RouteRule(object):
    """Represents a routing rule."""

    class vars(object):
        """Routing variables."""

        cookie = VarCookie
        geoip = VarGeoip
        httptime = VarHttptime
        metric = VarMetric
        query = VarQuery
        request = VarRequest
        time = VarTime
        uwsgi = VarUwsgi

    class var_functions(object):
        """Functions that can be applied to variables."""

        base64 = FuncBase64
        hex = FuncHex
        lower = FuncLower
        math = FuncMath
        mime = FuncMime
        upper = FuncUpper

    class stages(object):
        """During the request cycle, various stages (aka chains) are processed.

        Chains can be "recursive". A recursive chain can be called multiple times
        in a request cycle.

        """

        REQUEST = ''
        """Applied before the request is passed to the plugin."""

        ERROR = 'error'
        """Applied as soon as an HTTP status code is generate. **Recursive chain**."""

        RESPONSE = 'response'
        """Applied after the last response header has been generated (just before sending the body)."""

        FINAL = 'final'
        """Applied after the response has been sent to the client."""

    class subjects(object):
        """Routing subjects. These can be request's variables or other entities.

        .. note:: Non-custom subjects can be pre-optimized (during startup)
            and should be used for performance reasons.

        """
        custom = SubjectCustom

        http_host = SubjectHttpHost
        http_referer = SubjectHttpReferer
        http_user_agent = SubjectHttpUserAgent
        path_info = SubjectPathInfo
        query_string = SubjectQueryString
        remote_addr = SubjectRemoteAddr
        remote_user = SubjectRemoteUser
        request_uri = SubjectRequestUri
        status = SubjectStatus

    class transforms(object):
        """A transformation is like a filter applied to the response
        generated by your application.

        Transformations can be chained (the output of a transformation will be the input of the following one)
        and can completely overwrite response headers.

        * http://uwsgi.readthedocs.io/en/latest/Transformations.html

        """
        chunked = ActionChunked
        fix_content_len = ActionFixContentLen
        flush = ActionFlush
        gzip = ActionGzip
        template = ActionTemplate
        to_file = ActionToFile
        upper = ActionUpper

        # todo Consider adding the following and some others from sources (incl. plugins):
        # xslt, cachestore, memcachedstore, redisstore, rpc, lua

    class actions(object):
        """Actions available for routing rules.

        Values returned by actions:

            * ``NEXT`` - continue to the next rule
            * ``CONTINUE`` - stop scanning the internal routing table and run the request
            * ``BREAK`` - stop scanning the internal routing table and close the request
            * ``GOTO x`` - go to rule ``x``

        """
        add_var_cgi = ActionAddVarCgi
        add_var_log = ActionAddVarLog
        alarm = ActionAlarm
        auth_basic = ActionAuthBasic
        auth_ldap = AuthLdap
        dir_change = ActionDirChange
        do_break = ActionDoBreak
        do_continue = ActionDoContinue
        do_goto = ActionDoGoto
        fix_var_path_info = ActionFixVarPathInfo
        header_add = ActionHeaderAdd
        header_remove = ActionHeaderRemove
        headers_off = ActionHeadersOff
        headers_reset = ActionHeadersReset
        log = ActionLog
        offload_off = ActionOffloadOff
        redirect = ActionRedirect
        rewrite = ActionRewrite
        route_external = ActionRouteExternal
        route_uwsgi = ActionRouteUwsgi
        send = ActionSend
        serve_static = ActionServeStatic
        set_harakiri = ActionSetHarakiri
        set_script_file = ActionSetScriptFile
        set_uwsgi_process_name = ActionSetUwsgiProcessName
        set_var_document_root = ActionSetVarDocumentRoot
        set_var_path_info = ActionSetVarPathInfo
        set_var_remote_addr = ActionSetVarRemoteAddr
        set_var_remote_user = ActionSetVarRemoteUser
        set_var_request_method = ActionSetVarRequestMethod
        set_var_request_uri = ActionSetVarRequestUri
        set_var_script_name = ActionSetVarScriptName
        set_var_uwsgi_appid = ActionSetVarUwsgiAppid
        set_var_uwsgi_home = ActionSetVarUwsgiHome
        set_var_uwsgi_scheme = ActionSetVarUwsgiScheme
        signal = ActionSignal

        # todo Consider adding the following and some others from sources (incl. plugins):
        # cachestore, cacheset, memcached,
        # router_cache: cache, cache-continue, cachevar, cacheinc, cachedec, cachemul, cachediv
        # rpc,
        # rpc: call, rpcret, rpcnext, rpcraw, rpcvar,
        # access, spnego, radius
        # xslt, ssi, gridfs
        # cgi: cgi, cgihelper
        # router_access: access,
        # proxyhttp -router_http, proxyuwsgi -router_uwsgi, xattr -xattr
        # router_memcached: memcached, memcached-continue, memcachedstore
        # router_redis: redis, redis-continue, redisstore

    def __init__(self, action, subject=None, stage=stages.REQUEST):
        """
        :param RouteAction action: Action (or transformation) to perfrom.
            See ``.actions`` and ``.transforms``.

        :param SubjectCustom|SubjectBuiltin|str subject: Subject to verify before action is performed.
            See ``.subjects``.

            * String values are automatically transformed into ``subjects.path_info``.
            * If ``None`` action is performed always w/o subject check.

        :param str|unicode stage: Stage on which the action needs to be performed.
            See ``.stages``.

        """
        if subject is None:
            subject = 'run'  # always run the specified route action

        elif isinstance(subject, string_types):
            subject = self.subjects.path_info(subject)

        subject_rule = ''

        self._custom_subject = isinstance(subject, SubjectCustom)

        if self._custom_subject:
            subject_rule = subject
            subject = 'if-not' if subject.negate else 'if'

        elif isinstance(subject, SubjectBuiltin):
            subject_rule = subject.regexp
            subject = subject.name

        self.command_label = ('%s-route-label' % stage).strip('-')
        self.command = ('%s-route-%s' % (stage, subject)).strip('-')
        self.value = subject_rule, action


class Routing(OptionsGroup):
    """Routing subsystem.

    You can use the internal routing subsystem to dynamically alter the way requests are handled.

    .. note:: Since 1.9

    * http://uwsgi.readthedocs.io/en/latest/InternalRouting.html
    * http://uwsgi.readthedocs.io/en/latest/Transformations.html

    """

    route_rule = RouteRule

    class routers(object):
        """Dedicated routers, which can be used with `register_router()`."""

        http = RouterHttp
        https = RouterHttps
        ssl = RouterSsl
        fast = RouterFast
        raw = RouterRaw
        forkpty = RouterForkPty
        tuntap = RouterTunTap

    class modifiers(object):
        """Routing modifiers.

        * http://uwsgi.readthedocs.io/en/latest/Protocol.html

        """
        cache = ModifierCache
        cgi = ModifierCgi
        cluster_node = ModifierClusterNode
        config_from_node = ModifierConfigFromNode
        corerouter_signal = ModifierCorerouterSignal
        echo = ModifierEcho
        eval = ModifierEval
        example = ModifierExample
        fastfunc = ModifierFastfunc
        gccgo = ModifierGccgo
        glusterfs = ModifierGlusterfs
        gridfs = ModifierGridfs
        jvm = ModifierJvm
        legion_msg = ModifierLegionMsg
        lua = ModifierLua
        manage = ModifierManage
        manage_path_info = ModifierManagePathInfo
        message = ModifierMessage
        message_array = ModifierMessageArray
        message_marshal = ModifierMessageMarshal
        mono = ModifierMono
        multicast = ModifierMulticast
        multicast_announce = ModifierMulticastAnnounce
        persistent_close = ModifierPersistentClose
        php = ModifierPhp
        ping = ModifierPing
        psgi = ModifierPsgi
        rack = ModifierRack
        rados = ModifierRados
        raw = ModifierRaw
        reload = ModifierReload
        reload_brutal = ModifierReloadBrutal
        remote_logging = ModifierRemoteLogging
        response = ModifierResponse
        rpc = ModifierRpc
        signal = ModifierSignal
        snmp = ModifierSnmp
        spooler = ModifierSpooler
        ssi = ModifierSsi
        subscription = ModifierSubscription
        symcall = ModifierSymcall
        v8 = ModifierV8
        webdav = ModifierWebdav
        wsgi = ModifierWsgi
        xslt = ModifierXslt

    def use_router(self, router, force=None):
        """

        :param RouterBase router: Dedicated router object. See `.routers`.

        :param bool force: All of the gateways (routers) has to be run under the master process,
            supplying this you can try to bypass this limit.

        """
        self._set('force-gateway', force, cast=bool)

        router._contribute_to_opts(self)

        return self._section

    def register_route(self, route_rules, label=None):
        """Registers a routing rule.

        :param RouteRule|list[RouteRule] route_rules:

        :param str|unicode label: Label to mark the given set of rules.
            This can be used in conjunction with ``do_goto`` rule action.

            * http://uwsgi.readthedocs.io/en/latest/InternalRouting.html#goto

        """
        route_rules = listify(route_rules)

        if route_rules and label:
            self._set(route_rules[0].command_label, label, multi=True)

        for route_rules in route_rules:
            self._set(route_rules.command, route_rules.value, multi=True)

        return self._section

    def print_routing_rules(self):
        """Print out supported routing rules (actions, transforms, etc.)."""

        self._set('routers-list', True, cast=bool)

        return self._section

    def set_error_page(self, status, html_fpath):
        """Add an error page (html) for managed 403, 404, 500 response.

        :param int status: HTTP status code.

        :param str|unicode html_fpath: HTML page file path.

        """
        statuses = [403, 404, 500]

        status = int(status)

        if status not in statuses:
            raise ConfigurationError(
                'Code `%s` for `routing.set_error_page()` is unsupported. Supported: %s' %
                (status, ', '.join(map(str, statuses))))

        self._set('error-page-%s' % status, html_fpath, multi=True)

        return self._section

    def set_error_pages(self, codes_map=None, common_prefix=None):
        """Add an error pages for managed 403, 404, 500 responses.

        Shortcut for ``.set_error_page()``.

        :param dict codes_map: Status code mapped into an html filepath or
            just a filename if common_prefix is used.

            If not set, filename containing status code is presumed: 400.html, 500.html, etc.

        :param str|unicode common_prefix: Common path (prefix) for all files.

        """
        statuses = [403, 404, 500]

        if common_prefix:
            if not codes_map:
                codes_map = {code: '%s.html' % code for code in statuses}

            for code, filename in codes_map.items():
                codes_map[code] = os.path.join(common_prefix, filename)

        for code, filepath in codes_map.items():
            self.set_error_page(code, filepath)

        return self._section

    def set_geoip_params(self, db_country=None, db_city=None):
        """Sets GeoIP parameters.

        * http://uwsgi.readthedocs.io/en/latest/GeoIP.html

        :param str|unicode db_country: Country database file path.

        :param str|unicode db_city: City database file path. Example: ``GeoLiteCity.dat``.

        """
        self._set('geoip-country', db_country, plugin='geoip')
        self._set('geoip-city', db_city, plugin='geoip')

        return self._section

    def header_add(self, name, value):
        """Automatically add HTTP headers to response.

        :param str|unicode name:

        :param str|unicode value:

        """
        self._set('add-header', '%s: %s' % (name, value), multi=True)

        return self._section

    def header_remove(self, value):
        """Automatically remove specified HTTP header from the response.

        :param str|unicode value:

        """
        self._set('del-header', value, multi=True)

        return self._section

    def header_collect(self, name, target_var, pull=False):
        """Store the specified response header in a request var
        (optionally removing it from the response).

        :param str|unicode name:

        :param str|unicode target_var:

        :param bool pull: Whether to remove header from response.

        """
        self._set(
            'pull-header' if pull else 'collect-header',
            '%s %s' % (name, target_var), multi=True)

        return self._section
