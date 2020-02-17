from os import path

from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='robots',
    version='0.1',
    description='Robocode python clone',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jchacks/robots',
    author='jchacks',
    # author_email='flyingcircus@example.com',
    # license='MIT',
    packages=['robots'],
    install_requires=[
        'pygame',
        'numpy'
    ],
    include_package_data=True,
    zip_safe=False
)
