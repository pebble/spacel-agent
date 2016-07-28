from setuptools import setup, find_packages

requires = [
    'boto3==1.3.1',
    'botocore==1.4.13',
    'click==6.2',
    'docutils==0.12',
    'funcsigs==1.0.2',
    'futures==3.0.5',
    'jmespath==0.9.0',
    'mock==2.0.0',
    'pbr==1.9.1',
    'python-dateutil==2.5.3'
]

setup(name='spacel-agent',
      version='0.0.1',
      description='Space Elevator agent',
      long_description=open('README.md').read(),
      url='https://github.com/mycloudandme/spacel-agent',
      author='Pete Wagner',
      author_email='github@mycloudand.me',
      license='MIT',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['test']),
      install_requires=requires,
      zip_safe=True)
