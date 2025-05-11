import kopf
import kubernetes
import time

@kopf.on.create('example.com', 'v1', 'myresources')
def create_fn(spec, name, namespace, logger, **kwargs):
    image = spec.get('image', 'nginx:latest')
    pod = {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {'name': name},
        'spec': {
            'containers': [{'name': name, 'image': image}],
        },
    }
    api = kubernetes.client.CoreV1Api()
    api.create_namespaced_pod(namespace, pod)
    logger.info(f"Created Pod {name} with image {image}")

@kopf.on.delete('example.com', 'v1', 'myresources')
def delete_fn(name, namespace, logger, **kwargs):
    api = kubernetes.client.CoreV1Api()
    api.delete_namespaced_pod(name, namespace)
    logger.info(f"Deleted Pod {name}")
