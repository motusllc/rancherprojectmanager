![CI](https://github.com/motusllc/rancherprojectmanager/workflows/CI/badge.svg)

This project removes the obnoxious button-clicking process required to assign namespaces to projects within Rancher. This is helpful when dealing with clusters that might be rebuilt from scratch with some regularity, and/or environments where new namespaces are coming and going frequently

This app watches for namespace-modification events. If a namespace appears with our `--project-name-annotation`, we'll query Rancher to pick out the ID for the project with the matching name, and add it to the namespace, which is all Rancher needs to consider the namespace part of its project. 

If no project by that name exists, it's created. 

Project owners can also be managed with the --owners-annotation, see below. For this functionality to work, Rancher's API requires that this app use an auth token corresponding to a user account that has rights over the auth system being used. Thus, a local admin account's key can successfully handle Rancher-local users, but for Azure AD auth, the Rancher token needs to be created for the user who setup the Azure AD integration. 

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
               [-o OWNERS_ANNOTATION]

Watches and annotates namespaces to assign them to Rancher projects

optional arguments:
  -h, --help            show this help message and exit
  -a RANCHER_ADDR, --rancher-addr RANCHER_ADDR
                        Address of your rancher API. Include the protocol and
                        API path element (ex.
                        https://rancher.sandbox.motus.com/v3) (default: None)
  -k RANCHER_KEY, --rancher-key RANCHER_KEY
                        The name of your rancher API key (username) (default:
                        None)
  -s RANCHER_SECRET, --rancher-secret RANCHER_SECRET
                        The secret token of your rancher API key (password).
                        If omitted, this can instead loaded from a secret
                        mounted at /var/rancher-project-mgmt (default: None)
  -t PROJECT_NAME_ANNOTATION, --project-name-annotation PROJECT_NAME_ANNOTATION
                        The namespace annotation that this controller will
                        check for and act upon (default: rancher-project-
                        mgmt.motus.com/project-name)
  -p PROJECT_ID_ANNOTATION, --project-id-annotation PROJECT_ID_ANNOTATION
                        The annotation, typically controlled by Rancher, that
                        this controller will update to assign namespaces to
                        projects (default: field.cattle.io/projectId)
  -d DEFAULT_CLUSTER, --default-cluster DEFAULT_CLUSTER
                        The name of the cluster that new projects will be
                        created in, by default (default: local)
  -c CLUSTER_NAME_ANNOTATION, --cluster-name-annotation CLUSTER_NAME_ANNOTATION
                        The annotation used to specify what cluster a project
                        should be created in, if it doesn't already exist
                        (default: rancher-project-mgmt.motus.com/cluster-name)
  -o OWNERS_ANNOTATION, --owners-annotation OWNERS_ANNOTATION
                        The annotation that holds a comma-separated list of
                        groups or usernames, who will be granted owner on the
                        project for a namespace (default: rancher-project-
                        mgmt.motus.com/owners)
```