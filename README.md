# testFlask

## Test Flask is a simple application to describe more about the openshift development process and more
#### Code Adapted from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
 
### Steps to Run

*** Steps 1 & 2 are only necessary if you are using a private fit repo ***

- Create Secret in Openshift for Private/Cluster, example is for github ssh key
oc create secret generic $SECRET_NAME --type=kubernetes.io/ssh-auth --from-file=ssh-privatekey=$SSHKEY_PATH

- Link Secret with your Service Account,default on most Openshift projects i builder so will link with builder
oc secrets link builder $SECRET_NAME

- Create a new mysql instance(Application will use sqlite if no mysql detail is provided)
oc new-app $MYSQL_NAME MYSQL_USER=$MYSQL_USER MYSQL_PASSWORD=$MYSQL_PASSWORD MYSQL_DATABASE=$MYSQL_DB -l db=mysql -l app=flasktest

- Create a new application on openshift, using the oc new-app command. With the oc new-app command you have multiple options to specify how you would like to build a running container.Please see [Openshift Builds](https://docs.openshift.com/container-platform/4.3/builds/understanding-image-builds.html) and [Openshift S2i](https://docs.openshift.com/enterprise/3.2/using_images/s2i_images/python.html), *** Example below uses source-secret created earlier,if you want to use sqlite skip all the database environment variables ***

oc new-app python:3.6~git@github.com:MoOyeg/testFlask.git --source-secret=github-secret -l app=testapp --strategy=source  --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app --env=DATABASE_USERNAME=$MYSQL_USER --env=DATABASE_PASSWORD --env=DATABASE_HOST=$MYSQL_NAME --env=DATABASE_DB=$MYSQL_DB


