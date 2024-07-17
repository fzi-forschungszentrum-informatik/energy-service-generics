#!/bin/bash
# USAGE:
#
# Build `latest` images with:
# bash build-docker-images.sh 
#
# Build specific version, e.g. 0.1.0 with:
# bash build-docker-images.sh 0.1.0
set -euo pipefail

IMAGE_NAME="energy-service-generics"
SOURCE_PATH="./source"
IMAGE_TAG_BASE=${1:-latest}


# Build each of the four versions of the image and check directly 
# afterwards if the image works as expected by executing the tests.
# This way the script should fail faster if it doesn't make sense to
# build another version, as the tests will fail anyway to the problems
# already present in the the previous build.
# NOTE: The builds are in such an order that as much as possible of layers
#       can be reused to keep build times low.
docker build --target esg-base -t $IMAGE_NAME:${IMAGE_TAG_BASE} $SOURCE_PATH
docker run --rm -t $IMAGE_NAME:$IMAGE_TAG_BASE pytest /source/energy_service_generics/tests/
docker build --target esg-service -t $IMAGE_NAME:${IMAGE_TAG_BASE}-service $SOURCE_PATH
docker run --rm -t $IMAGE_NAME:${IMAGE_TAG_BASE}-service pytest /source/energy_service_generics/tests/
docker build --target esg-pandas -t $IMAGE_NAME:${IMAGE_TAG_BASE}-pandas $SOURCE_PATH
docker run --rm -t $IMAGE_NAME:${IMAGE_TAG_BASE}-pandas pytest /source/energy_service_generics/tests/
docker build --target esg-service-pandas -t $IMAGE_NAME:${IMAGE_TAG_BASE}-service-pandas $SOURCE_PATH
docker run --rm -t $IMAGE_NAME:${IMAGE_TAG_BASE}-service-pandas pytest /source/energy_service_generics/tests/

printf "\033[0;32m\n" # Make text green
printf "Success! "
printf "\033[0m" # Make text normal again.
printf "Built these images:\n"
echo $IMAGE_NAME:$IMAGE_TAG_BASE
echo $IMAGE_NAME:${IMAGE_TAG_BASE}-service
echo $IMAGE_NAME:${IMAGE_TAG_BASE}-pandas
echo $IMAGE_NAME:${IMAGE_TAG_BASE}-service-pandas
