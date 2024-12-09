# Example of a Client using ESG 

Example client to fetch a PV power generation forecast from the [Basic Example Service](https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/tree/main/docs/examples/basic_example) implemented with the [Generic Service Client](https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/main/source/esg/clients/service.py) provided in this package.

## Running the Client

In order to run the service simply use [docker compose](https://docs.docker.com/compose/gettingstarted/). As preliminary build the Energy Service Generics Docker images if not done already by executing. Assuming, that you are currently in the [folder of the basic example](https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/tree/main/docs/examples/basic_example/), build the images with:

```bash
cd ../../../
bash build-docker-images.sh
```

Then return in this directory and execute:

```bash
docker compose up
```

This service assumes that the that service is operated on the same machine as the client, i.e is reachable on `http://localhost:8800`. If you need to connect to a service operated somewhere else adjust the value of `SERVICE_BASE_URL` accordingly.
