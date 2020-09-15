# testFlask

## Test Flask is a simple flask application to show some parts of the openshift application process</br>
## Sample Envirtonment File included

 
### Steps to Run<br/>

1 **Create Necessary Projects**<br/>
```oc adm new-project $NAMESPACE_DEV```<br/>
```oc adm new-project $NAMESPACE_PROD```<br/>    

2 **Step 2 Only necessary if you are using a private repo**<br/>
**Create Secret in Openshift for Private/Cluster, example is for github ssh key**<br/>
```oc create secret generic $SECRET_NAME --type=kubernetes.io/ssh-auth --from-file=ssh-privatekey=$SSHKEY_PATH -n $NAMESPACE_DEV```

 Link Secret with your Service Account,the default Service account for builds is usually builder so will link with builder<br/>
```oc secrets link builder $SECRET_NAME -n $NAMESPACE_DEV```

3 **Create a New Secret to host our database credentials**<br/>
```oc create secret generic my-secret --from-literal=MYSQL_USER=$MYSQL_USER --from-literal=MYSQL_PASSWORD=$MYSQL_PASSWORD -n $NAMESPACE_DEV```

4 **Create a new mysql instance(Application will use sqlite if no mysql detail is provided)**<br/>
```oc new-app $MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE -l db=mysql -l app=testflask -n $NAMESPACE_DEV --as-deployment-config=true```

5 **The new app above will fail because we have not provided the MYSQL user and password,we can provide the database secret to the mysql deployment**<br/>
```oc set env dc/$MYSQL_HOST --from=secret/my-secret -n $NAMESPACE_DEV```

6 **Create a new application on openshift, using the oc new-app command. With the oc new-app command you have multiple options to specify how you would like to build a running container**.Please see [Openshift Builds](https://docs.openshift.com/container-platform/4.3/builds/understanding-image-builds.html) and [Openshift S2i](https://docs.openshift.com/enterprise/3.2/using_images/s2i_images/python.html), <br/>**Example below uses source-secret created earlier,if you want to use sqlite in the same pod instead of the mysql we created above skip all the database environment variables**</br>                                     - Private Repo with Source Secret<br/>  ```oc new-app python:3.6~git@github.com:MoOyeg/testFlask.git --name=$APP_NAME --source-secret=github-secret -l app=testflask --strategy=source  --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app --env=MYSQL_HOST=$MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE --as-deployment-config=true -n $NAMESPACE_DEV```<br/>
    - Public Repo without Source Secret(s2i Building)<br/> ```oc new-app https://github.com/MoOyeg/testFlask.git --name=$APP_NAME -l app=testflask --strategy=source --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app --env=MYSQL_HOST=$MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE --as-deployment-config=true -n $NAMESPACE_DEV```<br/>
    - Public Repo using the Dockerfile to build(Docker Strategy)<br/>```oc new-app https://github.com/MoOyeg/testFlask.git --name=$APP_NAME -l app=testflask --env=MYSQL_HOST=$MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE --as-deployment-config=true -n $NAMESPACE_DEV```<br/> 

7 **Expose the service to the outside world with an openshift route**<br/>
```oc expose svc/$APP_NAME -n $NAMESPACE_DEV```

8 **We can provide your database secret to your app deployment, so your app can use those details**<br/>
```oc set env dc/$APP_NAME --from=secret/my-secret -n $NAMESPACE_DEV```

9 **You should be able to log into the openshift console now to get a better look at the application, all the commands above can be run in the console, to get more info about the developer console please visit [Openshift Developer Console](https://docs.openshift.com/container-platform/4.4/applications/application_life_cycle_management/odc-creating-applications-using-developer-perspective.html)**

10 **To make the seperate deployments appear as one app in the Developer Console, you can label them. This step does not change app behaviour or performance is a visual aid and would not be required if app was created from developer console**<br/>
```oc label dc/$APP_NAME app.kubernetes.io/part-of=$APP_NAME -n $NAMESPACE_DEV```<br/>
```oc label dc/$MYSQL_HOST app.kubernetes.io/part-of=$APP_NAME -n $NAMESPACE_DEV```<br/>
```oc annotate dc/$APP_NAME app.openshift.io/connects-to=$MYSQL_HOST -n $NAMESPACE_DEV```<br/>

11 **You can attach a WebHook to your application , so when there is application code change the application is rebuilt to take adavantage of that, you can see steps to this via the developer console .Opensshift will create the html link and secret for you which you can configure in github/gitlab other generic VCS. See more here [Openshift Triggers](https://docs.openshift.com/container-platform/4.4/builds/triggering-builds-build-hooks.html) and see [github webhooks](https://developer.github.com/webhooks/)**<br/>
    -  To get the Webhook Link from the CLI<br/>
       ```oc describe bc/$APP_NAME | grep -i -A1 "webhook generic"```<br/>
    -  To get the Webhook Secret from the CLI<br/>
       ```oc get bc/$APP_NAME  -o jsonpath='{.spec.triggers[*].github.secret}'```<br/>
    - Content Type is application/json and disable ssl verification if your ingress does not have a trusted cert.<br/>


12 **It is important to be able to provide the status of your application to the platform so the platform does not send requests to application instances not ready or available to recieve them, this can be done with a liveliness and a health probe, please see [Health Checks](https://docs.openshift.com/container-platform/4.4/applications/application-health.html). This application has  sample /health and /ready uri that provide responses about the status of the application**<br/>

   - **Create a readiness probe for our application**<br/>
```oc set probe dc/$APP_NAME --readiness --get-url=http://:8080/ready --initial-delay-seconds=10 -n $NAMESPACE_DEV```<br/>

   - **Create a liveliness probe for our application**<br/>
```oc set probe dc/$APP_NAME --liveness --get-url=http://:8080/health --timeout-seconds=30 --failure-threshold=3 --period-seconds=10 -n $NAMESPACE_DEV```<br/>

   - **We can test Openshift Readiness by opening the application page and setting the application ready to down, after a while the application endpoint will be removed from the list of endpoints that recieve traffic for the service,you can confirm by**<br/>
      - ```oc get ep/$APP_NAME -n $NAMESPACE_DEV```<br/>
      - Since the readiness removes the pod endpoint from the service we will not be able to access the app page anymore<br/>
      - We will need to log into the pod to enable the readiness back <br/>
           - ```POD_NAME=$(oc get pods -l deploymentconfig=$APP_NAME -n $NAMESPACE_DEV -o name)```<br/>
           - Exec the Pod and curl the pod API to start the pod readiness<br/>
           - ```oc exec $POD_NAME curl http://localhost:8080/ready_down?status=up```<br/>
      
13 **Openshift also provides a way for you to use Openshift's platform monitoring to monitor your application metrics and provide alerts on those metrics.Note, this functionality is still in Tech Preview.This only works for applications that expose a /metrics endpoint that can be scraped which this application does. Please visit [Monitoring Your Applications](https://docs.openshift.com/container-platform/4.4/monitoring/monitoring-your-own-services.html) and you can see an example of how to do that [here](https://servicesblog.redhat.com/2020/04/08/application-monitoring-openshift/), before running any of the below steps please enable monitoring using info from the links above**<br/>

   - **Create a servicemonitor using below code <ins>(Please enable cluster monitoring with info from above first)</ins>, servicemonitor label must match label specified from the deployment config above.**<br/>

```
cat << EOF | oc create -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    k8s-app: prometheus-testflask-monitor
  name: prometheus-testflask-monitor
  namespace: $NAMESPACE_DEV
spec:
  endpoints:
  - interval: 30s
    targetPort: 8080
    scheme: http
  selector:
    matchLabels:
      app: $APP_NAME
EOF
```
<br/>

   - **After the servicemonitor is created we can confirm by looking up the application metrics under monitoring-->metrics, one of the metrics exposed is Available_Keys(Type Available_Keys in query and run) so as more keys are added on the application webpage we should see this metric increase**

   - **We can also create alerts based on Application Metrics using the Openshift's Platform AlertManager via Prometheus,[Openshift Alerting](https://docs.openshift.com/container-platform/4.4/monitoring/cluster_monitoring/managing-cluster-alerts.html).We need to create an Alerting Rule to recieve Alerts**

```
cat << EOF | oc create -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: testflask-alert
  namespace: $NAMESPACE_DEV
spec:
  groups:
  - name: $APP_NAME
    rules:
    - alert: DB_Alert
      expr: Available_Keys{job="testflask"} > 4
EOF
```
   - **The above alert should only fire when the we have more than 4 keys in the application, go to the application webpage and add more than 4 keys to the DB, we should be able to get an alert when we go to Monitoring-Alerts-AlertManager UI(Top of Page)**
#test
