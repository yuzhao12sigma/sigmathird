# -*- coding=utf-8 -*-

try:
    import setuptools
except ImportError:
    import distutils.core as setuptools


setuptools.setup(
    name="sigmathird",
    version="1.0",
    description="third party service for sending requests to sigmacloud",
    keywords="third party service",
    author="12Sigma Beijing",
    author_email="beijing@12sigma.ai",
    url="https://www.12sigma.ai/",
    packages=["sigmathird"],
    namespace_packages=["sigmathird"],
    include_package_data=True,
    install_requires=["pymongo==3.6.0",
                      "pyYAML==5.4",
                      "Flask==0.12.2",
                      "Flask-API==0.7.1",
                      "requests"]
)
