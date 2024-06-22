from setuptools import setup

setup(
    name='snappass',
    version='1.6.2',
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
    python_requires='>=3.8, <4',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    zip_safe=False,
)
