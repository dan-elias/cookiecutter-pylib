from contextlib import suppress
import json, pathlib, re, shutil, subprocess
import unittest

paths = {'tests': pathlib.Path(__file__).parent}
paths['project_root'] = paths['tests'].parent

with paths['project_root'].joinpath('cookiecutter.json').open('r') as in_stream:
    cookiecutter_args = json.load(in_stream)
paths['build'] = paths['project_root']/cookiecutter_args['app_name']
paths['build_code'] = paths['build']/cookiecutter_args['app_name']
paths['build_coverage_html'] = paths['build']/'htmlcov'

class Test_build(unittest.TestCase):
    @classmethod
    def shell_cmd(cls, cmd):
        return subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, cwd=paths['build'])
    @classmethod
    def setUpClass(cls):
        with suppress(FileNotFoundError):
            shutil.rmtree(paths['build'])
        subprocess.run('cookiecutter --no-input .', shell=True, check=True, cwd=paths['project_root'])
        cls.shell_cmd('./initialize.sh --test')
    @classmethod
    def tearDownClass(cls):
        with suppress(FileNotFoundError):
            shutil.rmtree(paths['build'])

class Test_build_no_delete(Test_build):
    def test_update_docs(self):
        self.shell_cmd('./update_docs.sh --test')
        html_build = paths['build']/'docs/build/html'
        self.assertTrue(html_build.joinpath('code_pages/example.html').exists())
        html_build_index = html_build/'index.html'
        self.assertTrue(html_build_index.exists())
        with html_build_index.open('r') as in_stream:
            index_html = in_stream.read()
        self.assertTrue('<li class="toctree-l1"><a class="reference internal" href="introduction.html">Introduction</a></li>' in index_html)
        self.assertTrue('<li class="toctree-l1"><a class="reference internal" href="code_pages/example.html">Example module</a></li>' in index_html)
        self.assertTrue('<li class="toctree-l1"><a class="reference internal" href="contributing.html">Contributing</a></li>' in index_html)
    def test_new_module(self):
        self.shell_cmd('./new_module.sh pkg1.mod1')
        self.assertTrue(paths['build_code'].joinpath('pkg1').exists())
        self.assertTrue(paths['build_code'].joinpath('pkg1/__init__.py').exists())
        self.assertTrue(paths['build_code'].joinpath('pkg1/mod1.py').exists())
        self.assertTrue(paths['build'].joinpath('tests/pkg1/__init__.py').exists())
        self.assertTrue(paths['build'].joinpath('tests/pkg1/test_mod1.py').exists())
        self.assertTrue(paths['build'].joinpath('docs/source/code_pages/pkg1.mod1.rst').exists())
    def test_bump_version(self):
        def get_build_version():
            version_rec = re.compile(r"__version__\s+=\s+'(?P<version>[^']+)'")
            with paths['build_code'].joinpath('__init__.py').open('r') as in_stream:
                return version_rec.search(in_stream.read()).groupdict()['version']
        self.assertEqual(get_build_version(), '0.0.1')
        self.shell_cmd('./bump_version.sh')
        self.assertEqual(get_build_version(), '0.0.2')
        self.shell_cmd('./bump_version.sh patch')
        self.assertEqual(get_build_version(), '0.0.3')
        self.shell_cmd('./bump_version.sh minor')
        self.assertEqual(get_build_version(), '0.1.0')
        self.shell_cmd('./bump_version.sh major')
        self.assertEqual(get_build_version(), '1.0.0')
    def test_coverage(self):
        file_names = ['_'.join(p.relative_to(paths['build_code'].parent).parts).replace('.', '_') + '.html' 
                      for p in paths['build_code'].glob('./**/*.py')]
        file_names.append('index.html')
        for file_name in file_names:
            self.assertFalse(paths['build_coverage_html'].joinpath(file_name).exists())
        self.shell_cmd('./coverage.sh')
        for file_name in file_names:
            self.assertTrue(paths['build_coverage_html'].joinpath(file_name).exists())

class Test_build_deletions(Test_build):
    def test_clear_examples(self):
        self.assertTrue(paths['build_code'].joinpath('example.py').exists())
        self.assertTrue(paths['build'].joinpath('tests/test_example.py').exists())
        self.assertTrue(paths['build'].joinpath('docs/source/code_pages/example.rst').exists())
        self.shell_cmd('./clear_examples.sh')
        self.assertFalse(paths['build_code'].joinpath('example.py').exists())
        self.assertFalse(paths['build'].joinpath('tests/test_example.py').exists())
        self.assertFalse(paths['build'].joinpath('docs/source/code_pages/example.rst').exists())

if __name__ == '__main__':
    unittest.main()
