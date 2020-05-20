# testFlask
#Code Adapted from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

Test Flask is a simple application to describe more about the openshift development process and more
 
Steps to Run

Steps 1 & 2 are only necessary if you are using a private GIT repo

1 Create Secret in Openshift for Private/Cluster, example is for github ssh key
oc create secret generic <secret_name> --type=kubernetes.io/ssh-auth --from-file=ssh-privatekey=<sshkey_path>

2 Link Secret with your Service Account,default on most Openshift projects i builder so will link with builder
oc secrets link builder <secret_name>

3 Create a new application on openshift, using the oc new-app command. With the oc new-app command you have multiple options to specify how you would like to build a running container.Please see 
will create:
     A deployment/deploymentconfig to manage the scaling of the app
     B If an appropriate source is provided it will automatically build the application. Notice in the example below I will not specify a builder image