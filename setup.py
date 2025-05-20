from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='tornet-multi-platform',
    version='2.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'requests[socks]',
        'pysocks'
    ],
    entry_points={
        'console_scripts': [
            'tornet=tornet.tornet:main',
        ],
    },
    author='Ernesto Leiva',
    author_email='contact@ernestoleiva.com',
    description='TorNet - Cross-platform IP rotation using Tor with logging and automation',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ErnestoLeiva/tornet-multi-platform',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Topic :: Internet :: Proxy Servers',
        'Topic :: Utilities'
    ],
    python_requires='>=3.6',
)
