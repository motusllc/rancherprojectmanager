This chart installs a Deployment of the rancherprojectmanager - see the full README at the repository for more info: https://github.com/motusllc/rancherprojectmanager/blob/master/README.md

The Rancher token secret is loaded into the container from a secret mount. You are expected to create the kube secret yourself, and specify the name with the corresponding `secretName` value below. 

Example kube secret YAML:
```yaml
apiVersion: 'kubernetes-client.io/v1'
kind: Secret
metadata:
  name: myRancherKubeSecret
type: Opaque
data:
  # rancher-secret is the required name here
  rancher-secret: SGFoYSwgeW91IGRpZG50IHRoaW5rIElkIGNoZWNrIGEgc2VjcmV0IGludG8gcHVibGljIHNvdXJj
ZSBjb2RlLCBkaWQgeW91Pwo= # echo mysecretvalue | base64
```

Example values: 
```yaml
rancherprojectmanager:
    rancherAddress: https://rancher.sandbox.motus.com/v3                         # Required
    rancherKey: token-abc123                                                     # Required
    secretName: myRancherKubeSecret                                              # Required
    projectNameAnnotation: rancher-project-mgmt.motus.com/project-name           # Defaults to this value
    projectIdAnnotation: field.cattle.io/projectId                               # Defaults to this value
    defaultCluster: local                                                        # Defaults to this value
    clusterNameAnnotation: rancher-project-mgmt.motus.com/cluster-name           # Defaults to this value
    ownersAnnotation: rancher-project-mgmt.motus.com/owners                      # Defaults to this value
    workloadManagersAnnotation: rancher-project-mgmt.motus.com/workload-managers # Defaults to this value
```

If you want to do something unusual in the container, you can also override the command altogether:
```yaml
rancherprojectmanager:
    # This will just launch the app like normal, with barebones arguments
    containerCommand: ./main.py --rancher-addr https://rancher.sandbox.motus.com/v3 --rancher-key token-abc12 --rancher-secret thisisntverysecure
```
