#

if [ "x$REGISTRY" == "x" ]; then

  echo Please pass the registry with REGISTRY=... bash buildx.sh
  exit 1
fi

docker buildx build \
	--push \
	--platform=linux/arm64,linux/amd64 \
	--tag "${REGISTRY}/sensormqtt" .

