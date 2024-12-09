# Example of a Minimal Service

Minimal client to fetch a PV power generation forecast from the [Basic Example Service](https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/tree/main/docs/examples/basic_example) implemented as simple shell script.

## Running the Client

To run the client in docker simply execute:

```bash
docker compose up
```

Local execution should work fine too, if `curl` and `jq` are installed, by calling:

```bash
bash ./source/client/main.sh
```

This service assumes that the that service is operated on the same machine as the client, i.e is reachable on `http://localhost:8800`. If you need to connect to a service operated somewhere else adjust the value of `SERVICE_BASE_URL` accordingly.

