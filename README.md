# testFlask

## Test Flask is a simple flask application to show some parts of the openshift application process
#### Code Adapted from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
 
### Steps to Run

**Steps 1 & 2 are only necessary if you are using a private fit repo**

- **Create Secret in Openshift for Private/Cluster, example is for github ssh key**<br/>
```oc create secret generic $SECRET_NAME --type=kubernetes.io/ssh-auth --from-file=ssh-privatekey=$SSHKEY_PATH -n $NAMESPACE```

- **Link Secret with your Service Account,the default Service account for builds is usually builder so will link with builder**<br/>
```oc secrets link builder $SECRET_NAME -n $NAMESPACE```

- **Create a New Secret to host our database credentials**<br/>
```oc create secret generic my-secret --from-literal=MYSQL_USER=$MYSQL_USER --from-literal=MYSQL_PASSWORD=$MYSQL_PASSWORD --from-literal=DATABASE_USER=$MYSQL_USER --from-literal=DATABASE_PASSWORD=$MYSQL_PASSWORD -n $NAMESPACE```

- **Create a new mysql instance(Application will use sqlite if no mysql detail is provided)**<br/>
```oc new-app $MYSQL_NAME --env=MYSQL_DATABASE=$MYSQL_DB -l db=mysql -l app=flasktest -n $NAMESPACE```

-**The new app above will fail because we have not provided the MYSQL user and password,we can provide the database secret to the mysql deployment**<br/>
```oc set env dc/$MYSQL_NAME --from=secret/my-secret -n $NAMESPACE```

- **Create a new application on openshift, using the oc new-app command. With the oc new-app command you have multiple options to specify how you would like to build a running container**.Please see [Openshift Builds](https://docs.openshift.com/container-platform/4.3/builds/understanding-image-builds.html) and [Openshift S2i](https://docs.openshift.com/enterprise/3.2/using_images/s2i_images/python.html), <br/>**Example below uses source-secret created earlier,if you want to use sqlite skip all the database environment variables**</br>```oc new-app python:3.6~git@github.com:MoOyeg/testFlask.git --name=$APP_NAME --source-secret=github-secret -l app=testapp --strategy=source  --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app --env=DATABASE_HOST=$MYSQL_NAME --env=DATABASE_DB=$MYSQL_DB -n $NAMESPACE```

- **Expose the service to the outside world with an openshift route**<br/>
```oc expose svc/$APP_NAME```

-**We can provide your database secret to your app deployment, so your app can use those details**<br/>
```oc set env dc/$APP_NAME --from=secret/my-secret -n $NAMESPACE```

- You should be able to log into the openshift console now to get a better look at the application, the whole process above can be done in the console, to get more info about the developer console please visit [Openshift Developer Console](https://docs.openshift.com/container-platform/4.4/applications/application_life_cycle_management/odc-creating-applications-using-developer-perspective.html)

- **To make the seperate deployments appear as one app in the Developer Console, you can label them. This step does not change app behaviour or performance is a visual aid and would not be required if app was created from developer console**
```oc label dc/$APP_NAME app.kubernetes.io/part-of=$APP_NAME```
```oc label dc/$MYSQL_NAME app.kubernetes.io/part-of=$APP_NAME```
```oc annotate dc/$APP_NAME app.openshift.io/connects-to=$MYSQL_NAME```

- **You can attach a WebHook to your application , so when there is application code change the application is rebuilt to take adavantage of that, you can see steps to this via the developer console .Opensshift will create the html link and secret for you which you can configure in github/gitlab other generic VCS. See more here [Openshift Triggers](https://docs.openshift.com/container-platform/4.4/builds/triggering-builds-build-hooks.html) and see [github webhooks](https://developer.github.com/webhooks/)**<br/>
    -  To get the Webhook Link from the CLI<br/>
       ```oc describe bc/$APP_NAME | grep -i -A1 "webhook generic"```
    -  To get the Webhook Secret from the CLI<br/>
       ```oc get bc/$APP_NAME  -o jsonpath='{.spec.triggers[*].github.secret}'```
    - Content Type is application/json and disable ssl verification if your ingress does not have a trusted cert.


- **It is important to be able to show case the status of your application to the platform so the platform does not send requests to application instances not ready to recieve them, this can be done with a liveliness and a health probe, please see [Health Checks](https://docs.openshift.com/container-platform/4.4/applications/application-health.html). This application has  sample /health and /ready uri that provide responses about the status of the application**<br/>

- **Create a readiness probe for our application**<br/>
oc set probe dc/$APP_NAME --readiness --get-url=http://:8080/ready --initial-delay-seconds=10

- **Create a liveliness probe for our application**<br/>
oc set probe dc/$APP_NAME --liveness --get-url=http://:8080/health --timeout-seconds=30 --failure-threshold=3 --period-seconds=10 -n $NAMESPACE




