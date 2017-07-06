import pytest
import os

from uwsgiconf import Section, Configuration
from uwsgiconf.exceptions import ConfigurationError


def test_section_basics(ini, assert_lines):

    my_section = Section()

    assert_lines('automatically generated', my_section)

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

    # bogus basic params handling. test for no error
    Section(
        basic_params_networking=None,
        basic_params_nonexistent={'a': 'b'},
        dummy_key=1,
    )


def test_section_print(assert_lines):

    assert_lines('%[[37;49mAAA a%[[0m', Section().print_out('a', indent='AAA '))
    assert_lines('%[[32;49m>   ===== variables', Section().print_variables())


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


def test_section_plugins(assert_lines):

    assert_lines([
        'plugin = plug',
        'autoload',
        'plugins-dir = /here',
        'plugins-dir = /there',
    ], Section().set_plugins_params(
        plugins='plug', search_dirs=['/here', '/there'], autoload=True
    ))


def test_plugin_init(assert_lines):
    assert_lines([
        'plugin = python33',

    ], Section().plugin_python.activate(version=33))

    # automatic activation
    assert_lines([
        'plugin = python34',

    ], Section(basic_params_plugin_python={'version': 34}))


def test_configuration(capsys, assert_lines):

    # basic params init
    assert_lines([
        'workers = 33',

    ], Section(basic_params_workers=dict(count=33)))

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

    assert Configuration([s1, s2]).print_ini()



