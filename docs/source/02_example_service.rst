Example service implementation
==============================
This section demonstrates a simple but fully functional implementation of a photovoltaic (PV) power gerneration forecast service. For more in-depth information about the individual components, please refer to the :doc:`01_concepts` section or the published `research article <https://de.overleaf.com/project/6565c3491f8923df81a997ac>`__.

1. Preparation of the forecast or optimization code
---------------------------------------------------
To implement a service, the code that is to be the payload of the service needs to be prepared. This code is responsible for the actual forecast or optimization task. In this example, the `pvlib <https://github.com/pvlib/pvlib-python>`__ has been utilized, which computes the PV power production forecast. As mentioned already though, the framework does not impose any restrictions on the code that is wrapped by it, i.e., linear programs, classical statistical models, or fully black-box machine learning approaches are all possible.

First the input data needs to be provided to the library. To keep this example simple, only the geographic position, i.e. latitude and longitude, as well as the geometry of the PV system, i.e. azimuth and inclination, and the peak power are selected to describe the PV system. The second part of the required input to compute PV power prediction consists of meteorological forecast data, especially forecasts of solar irradiance.

However, this example service is intended to produce PV power generation forecasts for systems for which geometry and peak power values may be unknown and need to be estimated from power production measurements. Therefore, the parameter fitting has been implemented with a simple least squares approach. Although it should be noted that this choice has no particular relevance for the present example. Thus, the input data necessary to obtain a forecast is separated into two groups: 

* **arguments**: here latitude and longitude
* **parameters**: here azimuth, inclination, and peak power

Finally, it should be considered that it may not be a good choice not to demand all input data as client input. In the present example, the service instead fetches the meteorological data automatically from a third-party web service, which would, in practice, make the interaction with the service more convenient and less error-prone for the client.

The actual format of input_data and output_data is implicitly defined in the corresponding data
models, which are introduced in the following section.

Below is an excerpt of the forecast code implemented in this exemplary service. Only the functions handle_request and fit_parameters are shown here, as they are the only part of the service implementation that actually interacts with the forecasting or optimization algorithm. The functions predict_pv_power, fetch_meteo_data as well as fit_with_least_squares have been omitted from the listing, as the practical implementation details of those are not necessary for a developer wanting to implement their service. However, the code of the omitted functions can be found in the repository of the `ESG framework <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics>`__.  Implementing fit_parameters is optional and can be omitted for services without fittable parameters. 

.. literalinclude:: ../examples/basic_example/source/service/fooc.py
   :pyobject: handle_request

.. literalinclude:: ../examples/basic_example/source/service/fooc.py
   :pyobject: fit_parameters

The code shown above can be found in the file `fooc.py <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/fooc.py>`__.

.. _data_model:

2. Definition of the data model
-------------------------------
The data model is the second component that is service specific and which must thus be defined by the service developer. The data models define the format of the data the client exchanges with the service. For a service without fittable parameters, i.e. a service with ``/request/`` endpoints only, it is sufficient to define the arguments required for computing the request as well as the result of the computation. The corresponding data models are called ``RequestArguments`` and ``RequestOutput``.

In the case of a service with fittable parameters, it is additionally necessary to define the data format for the input and output data of the ``/fit-parameters/`` endpoints. The data models specifying the input for the fitting process are referred to as ``FitParameterArguments`` and ``Observations``, and the corresponding output is ``FittedParameters``. As the simple PV power generation forecast service used as an example is designed to provide functionality to fit parameters, it is necessary to define all five data models.

.. literalinclude:: ../examples/basic_example/source/service/data_model.py
   :pyobject: RequestArguments

.. literalinclude:: ../examples/basic_example/source/service/data_model.py
   :pyobject: RequestOutput

.. literalinclude:: ../examples/basic_example/source/service/data_model.py
   :pyobject: Observations

.. literalinclude:: ../examples/basic_example/source/service/data_model.py
   :pyobject: FitParameterArguments
   
.. literalinclude:: ../examples/basic_example/source/service/data_model.py
   :pyobject: FittedParameters

The above code can be found in the `data_model.py <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/data_model.py>`__ file.

The ESG package provides ready-to-use **building blocks for data models**, which can be found in the file `metadata.py <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/source/esg/models/metadata.py>`__. For example, in the code above, ``GeographicPosition`` is imported from ESG. ``GeographicPosition`` is a data model itself, which defines that a geographic position consists of latitude and longitude. The data models also serve a documentational purpose as they define the data structure of the downstream application, i.e. the EMS. Additionally, they define permitted ranges for values, which helps in automatically validating the input provided by clients. 

3. Implementation of the worker component
-----------------------------------------
The worker component is responsible for executing the tasks, i.e. computing requests or fitting
parameters by invoking the forecasting or optimization code, as well as task scheduling. While the ESG framework utilizes the Celery library for implementing the worker, it extends it with functionality to make the implementation of services more convenient, for example by utilizing the data models for de-/serialization of input and output data. Thus, the main objective for implementing a worker is to wire up the data models with the forecasting or optimization code. This is usually a rather simple program, as displayed in the code excerpt below, taken from the PV power generation forecast example service.

.. literalinclude:: ../examples/basic_example/source/service/worker.py
   :pyobject: request_task

.. literalinclude:: ../examples/basic_example/source/service/worker.py
   :pyobject: fit_parameters_task

The above code can be found in the `api.py <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/worker.py>`__ file.

4. Customization of the API component
-------------------------------------
The implementation of the API component is available ready-to-use in the ESG framework. However, in order to operate the API it is necessary, similar to the worker, to wire up the API with the other components, in particular with the data model and the worker. Furthermore, some information like name and version number must be provided too. Nevertheless, the necessary code to instantiate an API component is fairly simple as seen in the code excerpt below.

.. literalinclude:: ../examples/basic_example/source/service/api.py
   :language: python
   :start-at: api =

The above code can be found in the `worker.py <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/service/api.py>`__ file.

5. Building docker images to derive functional services
-------------------------------------------------------
In order for the service developer to derive functional services, they need to build docker images that can be run e.g. on Kubernetes or Docker Swarm. It is necessary to build two distinct images, one for the API (which includes the data model) and one for the worker (which includes the data model and the forecasting or optimization code). The build instructions for both images are implemented as `Dockerfile <https://docs.docker.com/reference/dockerfile/>`__ as seen below.

.. literalinclude:: ../examples/basic_example/source/Dockerfile-API
.. literalinclude:: ../examples/basic_example/source/Dockerfile-worker

The above code can be found in the `Dockerfile-API <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/Dockerfile-API>`__ and the `Dockerfile-worker <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/docs/examples/basic_example/source/Dockerfile-worker>`__ files.
