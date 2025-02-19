Energy Service Generics Documentation
=====================================

Welcome to the documentation page of Energy Service Generics framework, a tool for the rapid implementation of forecasting and optimization services for energy management applications.

Energy Management Systems (EMSs) increase energy efficiency by computing optimized operational schedules and executing these on devices and systems. To that end they require forecasting and optimization algorithms. However, the development costs of target-specific algorithms generally outweigh the monetary savings they generate after deployment.
This is where the ESG framework comes in. It enables developers to wrap their existing forecasting or optimatization code as generic algorithms that are centrally provided as web services. This drastically reduces development costs. Furthermore, the framework does not impose any restrictions on the underlying forecasting or optimization algorithms, but rather provides a generic structure for the implementation of services.

First Things First
------------------
Please note this library relies heavily on Docker and Docker Compose. You may wish to familiarize yourself with these tools before using this library. A good starting point are the getting started pages of `Docker <https://docs.docker.com/get-started/>`__ and `Docker Compose <https://docs.docker.com/compose/gettingstarted/>`__ respectively.

.. note::
    This documentation is a work in progress. If you have any questions or suggestions, please feel free to contact us.

.. note::
    The code snippets in this documentation may not be up to date. Please refer to the `GitHub repository <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/>`__ for the most recent version.

Table of Contents
-----------------

.. toctree::
  :maxdepth: 3

  01_concepts.rst
  02_example_service.rst
  03_example_client.rst
  04_generic_tests.rst