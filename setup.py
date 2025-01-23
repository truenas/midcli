from setuptools import find_packages, setup

try:
    import fastentrypoints  # noqa
except ImportError:
    import sys
    print("fastentrypoints module not found. entry points will be slower.", file=sys.stderr)


setup(
    name='midcli',
    description='NAS Command Line Interface',
    packages=find_packages(),
    license='BSD',
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'console_scripts': [
            'cli = midcli.__main__:main',
            'cli_console = midcli.__main__:main_console',
        ],
    },
)
