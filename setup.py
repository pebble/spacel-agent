from setuptools import setup, find_packages

requires = [
    'boto3==1.3.1',
    'botocore==1.4.13',
    'docutils==0.12',
    'futures==3.0.5',
    'jmespath==0.9.0',
    'python-dateutil==2.5.3',
    'python-systemd==0.1-planning-0'
]

dependency_links = [
    'https://github.com/thepwagner/python-systemd/tarball/master#egg=0.1-planning-0'
]

setup(name='spacel-agent',
      version='0.0.1',
      description='Space Elevator agent',
      long_description=open('README.md').read(),
      url='https://github.com/mycloudandme/spacel-agent',
      author='Pete Wagner',
      author_email='github@mycloudand.me',
      dependency_links=dependency_links,
      license='MIT',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['test']),
      install_requires=requires,
      zip_safe=True)
