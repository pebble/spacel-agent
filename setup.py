from setuptools import setup, find_packages

setup(name='spacel-agent',
      version='0.0.1',
      description='Space Elevator agent',
      long_description=open('README.md').read(),
      url='https://github.com/pebble/spacel-agent',
      author='Pebble WebOps',
      author_email='webops@pebble.com',
      license='MIT',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['test']),
      install_requires=open('requirements.txt').read().splitlines(),
      zip_safe=True)
