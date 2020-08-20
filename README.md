![CI](https://github.com/motusllc/rancherprojectmanager/workflows/CI/badge.svg)

This project removes the obnoxious button-clicking process required to assign namespaces to projects within Rancher. This is helpful when dealing with clusters that might be rebuilt from scratch with some regularity, and/or environments where new namespaces are coming and going frequently

This app watches for namespace-modification events. If a namespace appears with our `--project-name-annotation`, we'll query Rancher to pick out the ID for the project with the matching name, and add it to the namespace, which is all Rancher needs to consider the namespace part of its project. 

If no project by that name exists, it's created. 


# Install via Helm

```shell
kubectl config use-context mycluster
kubectl create secret generic -n kube-system rancherprojectmanagersecret --from-literal=rancher-secret=mylongsecretstring
cd helm_chart
helm install -n kube-system rancher-project-manager rancher-project-manager --set rancherprojectmanager.rancherAddress=https://rancher.sandbox.motus.com/v3 --set rancherprojectmanager.rancherKey=token-abc123 --set rancherprojectmanager.secretName=rancherprojectmanagersecret
```

# Run Locally

## Install Dependencies

```
pip3 install -r requirements.txt
```

## Run Tests
```
python3 -m unittest discover . test_*.py
```

## Running

```
chmod +x main.py
./main.py --rancher-addr https://rancher.sandbox.motus.com/v3 --rancher-key token-abc12 --rancher-secret <redacted>
```

# Full Options
```shell
$ ./main.py --help
usage: main.py [-h] -a RANCHER_ADDR -k RANCHER_KEY [-s RANCHER_SECRET]
               [-t PROJECT_NAME_ANNOTATION] [-p PROJECT_ID_ANNOTATION]
               [-d DEFAULT_CLUSTER] [-c CLUSTER_NAME_ANNOTATION]

Watches and annotates namespaces to assign them to Rancher projects

optional arguments:
  -h, --help            show this help message and exit
  -a RANCHER_ADDR, --rancher-addr RANCHER_ADDR
                        Address of your rancher API. Include the protocol and
                        API path element (ex.
                        https://rancher.sandbox.motus.com/v3)
  -k RANCHER_KEY, --rancher-key RANCHER_KEY
                        The name of your rancher API key (username)
  -s RANCHER_SECRET, --rancher-secret RANCHER_SECRET
                        The secret token of your rancher API key (password).
                        If omitted, this can instead loaded from a secret
                        mounted at /var/rancher-project-mgmt
  -t PROJECT_NAME_ANNOTATION, --project-name-annotation PROJECT_NAME_ANNOTATION
                        The namespace annotation that this controller will
                        check for and act upon
  -p PROJECT_ID_ANNOTATION, --project-id-annotation PROJECT_ID_ANNOTATION
                        The annotation, typically controlled by Rancher, that
                        this controller will update to assign namespaces to
                        projects
  -d DEFAULT_CLUSTER, --default-cluster DEFAULT_CLUSTER
                        The name of the cluster that new projects will be
                        created in, by default
  -c CLUSTER_NAME_ANNOTATION, --cluster-name-annotation CLUSTER_NAME_ANNOTATION
                        The annotation used to specify what cluster a project
                        should be created in, if it doesn't already exist
```