from setuptools import setup

setup(
    name="medcat",
    version="2.0.0-beta",
    description="Compatibility layer for medcat2",
    py_modules=["medcat"],
    install_requires=["medcat2"],
)
