from setuptools import setup

setup(
    name="pdftool",
    version="0.1.0",
    py_modules=["main"],
    install_requires=["click", "pypdf"],
    entry_points={"console_scripts": ["pdftool = main:cli"]},
)
