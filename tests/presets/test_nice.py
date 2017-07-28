from uwsgiconf.presets.nice import Section, PythonSection


def test_nice_section(assert_lines):

    assert_lines([
        'workers = %k',

    ], Section())

    assert_lines([
        'workers = 13',
        'touch-reload', 'test_nice.py',

    ], Section(workers=13, touch_reload=__file__))


def test_nice_python(assert_lines):

    assert_lines([
        'plugin = python\npyhome = /home/idle/venv/\npythonpath = /home/idle/apps/',
        'wsgi = somepackage.module',

    ], PythonSection(
        params_python=dict(
            # We'll run our app using virtualenv.
            python_home='/home/idle/venv/',
            search_path='/home/idle/apps/',
        ),
        wsgi_module='somepackage.module',
    ))
