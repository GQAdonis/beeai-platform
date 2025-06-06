# Install with a list of agent images to deploy

Create the following yaml value files:

`providers.yaml`:

```yaml
providers:
  - location: <docker-image-id>
  - location: <docker-image-id>
```

Or use `../agent-registry.yaml` from this repository.

`variables.yaml`:

```yaml
variables:
  LLM_API_BASE: <url>
  LLM_API_KEY: <api-key>
  LLM_MODEL: <model-id>
```

In this directory run:

```shell
helm install -f <providers.yaml> -f <variables.yaml> <release-name> beeai-platform
```

Or with default providers and ollama:

```shell
helm install -f ../agent-registry.yaml -f variables.ollama.yaml <release-name> beeai-platform
```

Or provide secrets on the command line:

```shell
helm install \
  -f https://raw.githubusercontent.com/i-am-bee/beeai-platform/refs/heads/release-v0.2.0/agent-registry.yaml \
  --set variables.LLM_API_BASE=http://host.docker.internal:11434/v1 \
  --set variables.LLM_API_KEY=dummy \
  --set variables.LLM_MODEL=llama3.1:8b \
  my-release \
  beeai-platform
```

## External Services

### External S3 support

You may want to have beeai platform connect to an external storage streaming rather than installing seaweedfs inside
your cluster. To achieve this, the chart allows you to specify credentials for an external storage streaming with the
`externalS3`. You should also disable the seaweedfs installation with the `seaweedfs.enabled`
option. Here is an example:

```console
seaweedfs.enabled=false
externalS3.host=myexternalhost
exterernalS3.accessKeyID=accesskey
externalS3.accessKeySecret=secret
```