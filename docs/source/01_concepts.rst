Concepts
========
* Energy Management Systems (EMSs) increase energy efficiency by computing optimized operational schedules and executing these on devices and systems
* they require forecasting and optimization algorithms to effectively operate
* The development costs of target-specific algorithms generally outweigh the monetary savings they generate after deployment.
* Therefore, the ESG framework provides generic forecasting and optimization algorithms that are centrally provided as web services, drastically reducing development costs.
* This section explains how to apply the ESG framework and gives an overview of the basic technical concepts.
* For more in-depth information especially regarding the discussion of the approach, please refer to the published `research article <https://de.overleaf.com/project/6565c3491f8923df81a997ac>`__.

Framework
---------
* The figure shows the basic architecture of an EMS that integrates the ESG framework.

.. figure:: graphics/ems_architecture_with_services.png
   :alt: EMS Architecture
   :align: center

   EMS Architecture


* REST API
* main objectives
	* retrieve a forecast or optimized schedule
	* fit system specific parameters of a service
* Intended interaction with the API
	* POST request or fit-parameters
	* GET status of task (task_ID) (polling)
	* GET result of task (task_ID)
* authorization through JSON Web Tokens (JWTs)
* developers can specify the format of the input data for calls to /request/ and /fit-parameters/ and of the output returned by the corresponding /result/ API methods

Service Components
------------------
1. Base: Containing the components necessary for executing the code of the service.
2. Service Framework: Containing all components generic to all services.
3. Service Specific: Containing all components a service provider must implement to derive
a functional service.

.. figure:: graphics/service_components.png
   :alt: Service Components
   :align: center
   
   Service Components

* worker enables concurrent processing of requests, effectively decoupling the API from interacting with forecasting or optimization code
* worker and API should be operated in distinct processes to enhance performance
* connected through a message broker

.. figure:: graphics/service_architecture_full.png
   :alt: Full Service Architecture
   :align: center
   
   Full Service Architecture

    * For each valid POST request, API publishes a task on the message broker and assigns it an ID
    * A worker process fetches the task and starts computing the result
    * The worker regularly publishes status updates on the processing progress to the broker and finally the result of the computation
    * If the /status/ endpoint is called, the API fetches the latest update regarding the corresponding task and returns the information to the client
    * If the /result/ endpoint is called, the API fetches the result from the broker and returns it to the client 
    * garbage collector deletes task-related data from the broker that are likely not required anymore (DOES THE USER DEFINE WHEN A TASK IS DELETED?)

Operation Concepts
------------------
* Processes of the service need to be wrapped in Docker containers
* Commercial applications should select Kubernetes as orchestrator of the containers and academic applications Docker swarm
* Supportive applications required
	* gateway (aka ingress or reverse proxy): makes the API containers accessible to the EMS and balances the distribution of requests across the API containers. Ideally, takes care of encrypting the communication between the client and the service through HTTPS.
	* Identity Provider (IdP): Issues the JWT tokens to the client software using the OpenID Connect (OIDC) protocol (e.g. Keycloak)


Open Source Community
---------------------
* possibility of extending the service with different algorithms potentially even unrelated to energy management 
