from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.readlines()

setup(
    name='myawesomepackage',
    version='0.1',
    packages=find_packages(),
    url='https://example.com',
    author='abdusco',
    description='',
    install_requires=requirements,
    entry_points=dict(console_scripts=[
        'myawesomeapp=app:main'
    ])
)