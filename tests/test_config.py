import os
from tempfile import NamedTemporaryFile
import pytest

from uwsgiconf import Section, Configuration
from uwsgiconf.exceptions import ConfigurationError


def test_section_basics(assert_lines):

    my_section = Section()

    assert_lines('automatically generated', my_section, stamp=True)

    my_section.set_basic_params(strict_config=True)

    assert_lines([
        'uwsgi',
        'strict',
    ], my_section)

    # unset bool
    my_section.set_basic_params(strict_config=False)
    assert_lines([
        'strict',
    ], my_section, assert_in=False)

    # successive unset bool
    my_section.set_basic_params(strict_config=False)

    assert_lines('plugins-list = true', Section().print_plugins())

    # __call__ -> set_basic_params
    assert_lines('workers = 10', Section().workers(count=10))

    # bogus basic params handling. test for no error
    Section(
        params_networking=None,
        params_nonexistent={'a': 'b'},
        dummy_key=1,
    )


def test_section_embeddeding_plugins(assert_lines, mock_popen):
    # Embedded plugins handling.
    section = Section(embedded_plugins=Section.embedded_plugins_presets.BASIC)
    assert_lines([
        'plugin = syslog'
    ], section.logging.add_logger(section.logging.loggers.syslog('some')), assert_in=False)

    mock_popen(lambda: ('plugins ***\nsyslog', ''))

    # Probing.
    section = Section(embedded_plugins=Section.embedded_plugins_presets.PROBE)
    assert_lines([
        'plugin = syslog'
    ], section.logging.add_logger(section.logging.loggers.syslog('some')), assert_in=False)

    section = Section(embedded_plugins=Section.embedded_plugins_presets.PROBE('/venv/bin/uwsgi'))
    assert_lines([
        'plugin = syslog'
    ], section.logging.add_logger(section.logging.loggers.syslog('some')), assert_in=False)


def test_section_print(assert_lines):

    assert_lines('%[[37;49mAAA a%[[0m', Section(style_prints=True).print_out('a', indent='AAA '))
    assert_lines('= >   ===== variables', Section().print_variables())


def test_section_fallback(assert_lines):

    assert_lines('fallback-config = a/b.ini', Section().set_fallback('a/b.ini'))
    assert_lines('fallback-config = :here', Section().set_fallback(Section(name='here')))


def test_section_env(assert_lines):
    os.environ['Q'] = 'qq'

    assert_lines([
        'env = A=aa',
        'unenv = B',
        'env = Q=qq',
    ], Section().env('A', 'aa').env('Q').env('B', unset=True))


def test_section_include(assert_lines):

    assert_lines('ini = a/b.ini', Section().include('a/b.ini'))
    assert_lines('ini = :here', Section().include(Section(name='here')))


def test_section_derive_from(assert_lines):
    sec_base = Section(name='mine').workers.set_basic_params(count=3)

    assert_lines([
        '[mine]',
        'workers = 3',
    ], sec_base)

    sec1 = (
        Section.derive_from(sec_base).
            workers.set_basic_params(count=4).master_process.set_basic_params(enable=True))

    sec2 = (
        Section.derive_from(sec_base, name='other').
            workers.set_thread_params(enable=True))

    assert_lines([
        '[mine]',
        'workers = 4',
    ], sec1)

    assert_lines([
        '[other]',
        'workers = 3',
        'enable-threads = true',
    ], sec2)


def test_section_plugins(assert_lines):

    assert_lines([
        'plugins-dir = /here\nplugins-dir = /there\nplugin = plug',
    ], Section().set_plugins_params(
        plugins='plug', search_dirs=['/here', '/there'], autoload=True
    ))




def test_plugin_init(assert_lines):
    assert_lines([
        'plugin = python34',

    ], Section(params_python={'version': 34, 'python_home': '/here'}))


def test_configuration(capsys, assert_lines):

    # basic params init
    assert_lines([
        'workers = 33',

    ], Section(params_workers=dict(count=33)))

    assert Section().as_configuration().tofile()

    fpath = NamedTemporaryFile(delete=False).name

    assert fpath == Section().as_configuration().tofile(fpath)

    s1 = Section()
    s2 = 'some'

    with pytest.raises(ConfigurationError) as einfo:
        Configuration([s1, s2]).format()
    assert 'Section' in str(einfo.value)  # is a section

    s2 = Section()

    with pytest.raises(ConfigurationError) as einfo:
        Configuration([s1, s2]).format()
    assert 'unique' in str(einfo.value)  # has unique name

    s2.name = 'another'

    assert 'ini = :another' in Configuration([s1, s2], autoinclude_sections=True).format()

    assert Configuration([s1, s2]).print_ini()
