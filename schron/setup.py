from setuptools import setup, find_packages

setup(
    name='schron',
    version='0.1.2',
    packages=find_packages(),
    install_requires=[
        'click',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'schron=schron.cli:main',
        ],
    },
    description='CLI утилита для управления Secret API',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
