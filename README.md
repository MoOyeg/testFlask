# testFlask
#Code Adapted from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

Test Flask is a simple application to describe more about the openshift development process and more
 
Steps to Run

Steps 1 & 2 are only necessary if you are using a private GIT repo

1 Create Secret in Openshift for Private/Cluster, example is for github ssh key
oc create secret generic <secret_name> --type=kubernetes.io/ssh-auth --from-file=ssh-privatekey=<sshkey_path>

2 Link Secret with your Service Account,default on most Openshift projects i builder so will link with builder
oc secrets link builder <secret_name>

3 Create a new application on openshift, using the oc new-app command. With the oc new-app command you have multiple options to specify how you would like to build a running container.Please see https://docs.openshift.com/container-platform/4.3/builds/understanding-image-builds.html and https://docs.openshift.com/enterprise/3.2/using_images/s2i_images/python.html

oc new-app git@github.com:MoOyeg/testFlask.git --source-secret=github-secret -l app=testapp-git --strategy=source --build-env=APP_CONFIG=gunicorn.conf.py --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app


oc create secret generic testappflask --from-literal=SQLALCHEMY_DATABASE_URI=mysql://user:pass@mysql/testdb app=testappflask