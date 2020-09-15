from setuptools import setup

setup(
    name='snappass',
    version='1.5.0',
    description="It's like SnapChat... for Passwords.",
    long_description=(open('README.rst').read() + '\n\n' +
                      open('AUTHORS.rst').read()),
    url='http://github.com/Pinterest/snappass/',
    install_requires=['Flask', 'redis', 'cryptography'],
    license='MIT',
    author='Dave Dash',
    author_email='dd+github@davedash.com',
    packages=['snappass'],
    entry_points={
        'console_scripts': [
            'snappass = snappass.main:main',
        ],
    },
    include_package_data=True,
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    zip_safe=False,
)
