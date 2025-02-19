Example client implementation
=============================
This section showcases two example client implementations for the basic example service. The first example is a minimal client implemented in a UNIX shell script. The second example is a more sophisticated client implemented in Python using the ESG package. 

Minimal client implementation
----------------------------------------------
This minimal client implementation is to be executed on the same machine as the service. The service should be reachable via a localhost port. The client is implemented using a simple UNIX shell script and requires the additional packages **curl** and **jq**. The script below can be used to simulate a client that requests a photovoltaic power generation forecast from the basic example service. Note that this interaction with the `/fit-parameters/` endpoint is omitted in this example but would follow the same structure.

.. literalinclude:: ../examples/minimial_client/source/client/main.sh
    :language: bash
    :start-at: SERVICE_BASE_URL

Client implementation in python
-------------------------------
The service integration in a production EMS will probably require a more sophisticated client implementation and require additional functionality. However, the concept of the client remains the same. As mentioned before, the ESG package contains a `generic client <https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/source/esg/clients/service.py>`__ providing additional functionality such as parsing the result into the format the EMS expects and network error handling.

.. literalinclude:: ../examples/client_using_ESG/source/client/main.py
    :language: python
    :start-at: import

It is recommended that the client developer specifies the data models themself in order to document the data structure of the downstream application, i.e. the EMS.  This should reduce tedious debugging deep within the downstream application and produce the error right inside the client code. However, it is possible to fetch the data models autommatically from the service.

It is to be noted, that the generic client provided by the ESG package can only be used in a python environment. Nevertheless, if the client code needs to be in a different language it should be possible to implement the logic rather quickly.  `Swagger Codegen <https://swagger.io/tools/swagger-codegen/>`__ can help to partially automate the generation of the client program.