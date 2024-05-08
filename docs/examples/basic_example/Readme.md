# Basic Example Service

This is the fundamental example that demonstrates how to build a service from existing forecasting or optimization code. More details are provided in the corresponding documentation.

## Running the Service 

In order to run the service simply use [docker compose](https://docs.docker.com/compose/gettingstarted/). As preliminary build the Energy Service Generics Docker images if not done already by executing. Assuming, that you are currently in the [folder of the basic example](https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/tree/main/docs/examples/basic_example/), build the images with:

```bash
bash ../../../build-docker-images.sh
```

Then run

```bash
docker compose up
```

in this directory. You should now be able to view the interactive documentation of the API component at http://localhost:8800/.

Press `Ctrl` + `c` to stop the service and execute

```bash
docker compose down
```

to remove the containers.

## Running the Tests / Working on the Service Code

The Energy Service Generics follows a [Test Driven Development](https://en.wikipedia.org/wiki/Test-driven_development) pattern with all tests being executed inside containers to make the results independent of the machine they are executed on. Furthermore, the Energy Service Generics uses an *autotest* approach, i.e. that tests are automatically executed one of the source files has been changed and saved. In order to launch the autotest container use:

```
docker compose -f docker-compose-autotest.yml up --no-log-prefix
```



