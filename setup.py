from setuptools import setup, find_packages

setup(
    name="game_ai",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'opencv-python>=4.8.0',
        'mss>=9.0.1',
        'numpy>=1.24.0',
        'pyyaml>=5.4.0',
    ]
) 