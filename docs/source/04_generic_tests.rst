Generic Tests
=============
The ESG package provides a set of generic tests that can be used to verify the correct implementation of a service. All tests can be found in the `test directory <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/tree/main/source/tests>`__. The tests are implemented using the `pytest <https://docs.pytest.org/en/stable/>`__ framework.

Below is an example implementation of tests for the basic example service detailed in :doc:`02_example_service`.

Mock server for third-party services
------------------------------------
The example service uses the third-party service `Open-Meteo <https://open-meteo.com/>`__ to fetch meteorological data. To avoid the dependency on this service, a mock server is used in the tests. The server is started before the tests are executed and shut down afterwards. It is set up to return predefined data when requested. The data is stored in a python file and loaded into the mock server before the tests are executed (see :ref:`mock_data`).

.. literalinclude:: ../examples/basic_example/source/service/tests/conftest.py
    :start-at: import

.. _mock_data:

Preparation of mock data
------------------------
In addition to the response data for the mocked Open-Meteo request, the `data.py file <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/tests/data.py>`__ should always contain the following data.

* **Mock data for testing the /request/ and the /fit-parameters/ endpoints** 
  (`fooc.py <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/fooc.py>`__ functions in the basic example):
    * The expected ``/request/`` inputs, i.e., the ``RequestArguments`` as ``REQUEST_INPUTS_FOOC_TEST``
    * The expected ``/fit-parameters/`` inputs, i.e., the ``FitParameterArguments`` and the ``Observations`` as ``FIT_PARAM_INPUTS_FOOC_TEST`` consisting of ``arguments`` and ``observations``
    * The expected outputs, i.e., the ``RequestOutput`` and the ``FittedParameters`` as ``REQUEST_OUTPUTS_FOOC_TEST`` and ``FIT_PARAM_OUTPUTS_FOOC_TEST``
* **Mock data for testing the input and output data models for the /request/ and the /fit-parameters/ endpoints**
  (`data_model.py <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/data_model.py>`__ file in the basic example):
    * A **valid object** of the ``RequestArguments`` class as ``REQUEST_INPUTS_MODEL_TEST`` and the corresponding valid output object as ``REQUEST_OUTPUTS_MODEL_TEST``
    * A **valid object** of the ``FitParameterArguments`` and the ``Observations`` class as ``FIT_PARAM_INPUTS_MODEL_TEST`` consisting of ``arguments`` and ``observations`` and the corresponding valid output object as ``FIT_PARAM_OUTPUTS_MODEL_TEST``
    * An **invalid object** of the ``RequestArguments`` class as ``INVALID_REQUEST_INPUTS`` and the corresponding invalid output as ``INVALID_REQUEST_OUTPUTS``
    * An **invalid object** of the ``FitParameterArguments`` and the ``Observations`` class as ``INVALID_FIT_PARAM_INPUTS`` consisting of ``arguments`` and ``observations`` and the corresponding invalid output as ``INVALID_FIT_PARAM_OUTPUTS``

Testing the forecast and optimization code
------------------------------------------
The tests for the forecast and optimization code are implemented in the `test_fooc.py file <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/tests/test_fooc.py>`__. To test the ``/request/`` and the ``/fit-parameters/`` endpoints, the service specific data models are used as well the ``GenericFOOCTest``, which is included in the `generic tests <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/source/esg/test/generic_tests.py>`__ provided by the ESG package. As the code excerpt below shows, implementing the tests is thus fairly simple.

.. literalinclude:: ../examples/basic_example/source/service/tests/test_fooc.py
    :start-at: RequestInput

The tests included in the generic tests only cover basic scenarios. Developers will likely want to add more sophisticated tests for their forecasting or optimization code.

The tests for the third-party service Open-Meteo is omitted as the implementation details are likely to vary from service to service. However, the tests for the Open-Meteo service can be found in the `test_fooc.py file <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/tests/test_fooc.py>`__ as well.

Testing the specified data models
---------------------------------
In order to enure that the data models are well defined, the input and output data models for the ``/request/`` and the ``/fit-parameters/`` endpoints are tested. These tests utilize the ``GenericMessageSerializationTest`` included in the `generic tests <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/source/esg/test/generic_tests.py>`__ provided by the ESG package is used. Due to the generic tests, the implementation is fairly simple.

.. literalinclude:: ../examples/basic_example/source/service/tests/test_data_model.py
    :start-at: RequestInput
    :end-before: FitParametersInput

.. literalinclude:: ../examples/basic_example/source/service/tests/test_data_model.py
    :start-at: FitParametersInput

The code excerpt above can be found in the `test_data_model.py <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/tests/test_data_model.py>`__ file.

Testing the worker component
----------------------------
To ensure worker component is correctly implemented, the ``GenericWorkerTaskTest`` included in the `generic tests <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/source/esg/test/generic_tests.py>`__ provided by the ESG package is used. The tests for the worker component are implemented in the `test_worker.py file <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/tests/test_worker.py>`__. As the code excerpt below shows, the implementation is again quite easy.

.. literalinclude:: ../examples/basic_example/source/service/tests/test_worker.py
    :pyobject: TestRequestTask

.. literalinclude:: ../examples/basic_example/source/service/tests/test_worker.py
    :pyobject: TestFitParametersTask


Testing the API component
-------------------------
Finally, the api component needs to be tested for correct implementation. For this purpose, the ESG package's `generic tests <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/source/esg/test/generic_tests.py>`__ provide the ``GenericAPITest``. Again, the implementation is quite simple as demonstrated below.

.. literalinclude:: ../examples/basic_example/source/service/tests/test_api.py
    :start-at: RequestInput

The tests for the api component can be found in the `test_api.py file <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/tests/test_api.py>`__.