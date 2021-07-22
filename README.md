# testFlask

#This Branch tests the Quart Framework instead of Flask
## Test Flask is a simple flask application to show some parts of the openshift application process.  It's been broken down into a series of modules that cover likely Openshift Use Cases</br>
----------
## Modules
### Module 1: testFlask - Main Application(This Page)

  1. [s2i Build](https://github.com/MoOyeg/testFlask#source-environment-variables)<br/>
  2. [Git Webhooks](https://github.com/MoOyeg/testFlask#webhooks)<br/>
  3. [Openshift Health Checks](https://github.com/MoOyeg/testFlask#health-checks)<br/>
  4. [Horizontal Autoscaling](https://github.com/MoOyeg/testFlask#horizontal-autoscaling-with-cpumemory)<br/>
  5. [Vertical Autoscaling](https://github.com/MoOyeg/testFlask#vertical-pod-autoscaler)<br/>
  6. [User Workload Monitoring](https://github.com/MoOyeg/testFlask#monitoring-and-autoscaling-application-metrics)<br/>
  7. [Serverless Example](https://github.com/MoOyeg/testFlask#openshift-serverless)<br/>

### Module 2: [testFlask-Jenkins](https://github.com/MoOyeg/testFlask-Jenkins) - Create Same Application with a Jenkins Pipeline in Openshift

### Module 3: [testFlask-Tekton](https://github.com/MoOyeg/testFlask-tekton) - Create Same Application with a Tekton Pipeline in Openshift

### Module 4: [testFlask-Oauth](https://github.com/MoOyeg/testFlask-Oauth-Proxy) - Application authentication using Openshift Oauth Proxy<br/>

### Module 5: [testflask-gitops](https://github.com/MoOyeg/testflask-gitops) - ArgoCD Application Continous Deployment<br/>

### Module 6: [testflask-helm-repo](https://github.com/MoOyeg/testflask-helm-repo) - Deploy the Same Application via Helm<br/>
<br/>


### Steps to Run<br/>

### Source Environment Variables
`eval "$(curl https://raw.githubusercontent.com/MoOyeg/testFlask/master/sample_env)"`

1 **Create Necessary Projects**<br/>
```oc adm new-project $NAMESPACE_DEV```<br/>
```oc adm new-project $NAMESPACE_PROD```<br/>    

2 **Step 2 Only necessary if you are using a private repo**<br/>
**Create Secret in Openshift for Private/Cluster, example is for github ssh key**<br/>
```oc create secret generic $REPO_SECRET_NAME --type=kubernetes.io/ssh-auth --from-file=ssh-privatekey=$SSHKEY_PATH -n $NAMESPACE_DEV```

 Link Secret with your Service Account,the default Service account for builds is usually builder so will link with builder<br/>
```oc secrets link builder $REPO_SECRET_NAME -n $NAMESPACE_DEV```

3 **Create a New Secret to host our database credentials**<br/>
```oc create secret generic my-secret --from-literal=MYSQL_USER=$MYSQL_USER --from-literal=MYSQL_PASSWORD=$MYSQL_PASSWORD -n $NAMESPACE_DEV```

4 **Create a new mysql instance(Application will use sqlite if no mysql detail is provided)**<br/>
```oc new-app $MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE -l db=mysql -l app=testflask -n $NAMESPACE_DEV --as-deployment-config=true```

5 **The new app above will fail because we have not provided the MYSQL user and password,we can provide the database secret to the mysql deployment**<br/>
```oc set env dc/$MYSQL_HOST --from=secret/my-secret -n $NAMESPACE_DEV```

6 **Create a new application on openshift, using the oc new-app command. With the oc new-app command you have multiple options to specify how you would like to build a running container**.Please see [Openshift Builds](https://docs.openshift.com/container-platform/4.3/builds/understanding-image-builds.html) and [Openshift S2i](https://docs.openshift.com/enterprise/3.2/using_images/s2i_images/python.html), <br/>**Example below uses source-secret created earlier,if you want to use sqlite in the same pod instead of the mysql we created above skip all the database environment variables**</br>                                     
- Private Repo with Source Secret<br/>  
```oc new-app python:3.6~git@github.com:MoOyeg/testFlask.git --name=$APP_NAME --source-secret$REPO_SECRET_NAME -l app=testflask --strategy=source  --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app --env=MYSQL_HOST=$MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE --as-deployment-config=true -n $NAMESPACE_DEV```<br/>
- Public Repo without Source Secret(s2i Building)<br/> 
```oc new-app https://github.com/MoOyeg/testFlask.git --name=$APP_NAME -l app=testflask --strategy=source --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app --env=MYSQL_HOST=$MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE --as-deployment-config=true -n $NAMESPACE_DEV```<br/>
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

## Webhooks
11 **You can attach a WebHook to your application , so when there is application code change the application is rebuilt to take adavantage of that, you can see steps to this via the developer console .Opensshift will create the html link and secret for you which you can configure in github/gitlab other generic VCS. See more here [Openshift Triggers](https://docs.openshift.com/container-platform/4.4/builds/triggering-builds-build-hooks.html) and see [github webhooks](https://developer.github.com/webhooks/)**<br/>
    -  To get the Webhook Link from the CLI<br/>
       ```oc describe bc/$APP_NAME | grep -i -A1 "webhook generic"```<br/>
    -  To get the Webhook Secret from the CLI<br/>
       ```oc get bc/$APP_NAME  -o jsonpath='{.spec.triggers[*].github.secret}'```<br/>
    - Content Type is application/json and disable ssl verification if your ingress does not have a trusted cert.<br/>

## Health Checks
12 **It is important to be able to provide the status of your application to the platform so the platform does not send requests to application instances not ready or available to recieve them, this can be done with a liveliness and a health probe, please see [Health Checks](https://docs.openshift.com/container-platform/4.4/applications/application-health.html). This application has  sample /health and /ready uri that provide responses about the status of the application**<br/>

   - **Create a readiness probe for our application**<br/>
```oc set probe dc/$APP_NAME --readiness --get-url=http://:8080/ready --initial-delay-seconds=10 -n $NAMESPACE_DEV```<br/>

   - **Create a liveliness probe for our application**<br/>
```oc set probe dc/$APP_NAME --liveness --get-url=http://:8080/health --timeout-seconds=30 --failure-threshold=3 --period-seconds=10 -n $NAMESPACE_DEV```<br/>

   - **We can test Openshift Readiness by opening the application page and setting the application ready to down, after a while the application endpoint will be removed from the list of endpoints that recieve traffic for the service,you can confirm by**<br/>
      - ```oc get ep/$APP_NAME -n $NAMESPACE_DEV```<br/>
      - Since the readiness removes the pod endpoint from the service we will not be able to access the app page anymore<br/>
      - We will need to log into the pod to enable the readiness back <br/>
           - ```POD_NAME=$(oc get pods -l deploymentconfig=$APP_NAME -n $NAMESPACE_DEV -o name | head -n 1)```<br/>
           - Exec the Pod and curl the pod API to start the pod readiness<br/>
           - ```oc exec $POD_NAME curl http://localhost:8080/ready_down?status=up```<br/>

   - **We can test Openshift Liveliness also, when a pod fails it's liveliness check, it is restarted based on the parameters used in the liveliness check, see liveliness probe command above**<br/>
          - Set the Pod's liveliness to down<br/>
           - ```POD_NAME=$(oc get pods -l deploymentconfig=$APP_NAME -n $NAMESPACE_DEV -o name | head -n 1)```<br/>
           - ```oc exec $POD_NAME curl http://localhost:8080/health_down?status=down```<br/>

## Horizontal AutoScaling with CPU/Memory
13 **Autoscale based on Pod CPU Metrics**<br/>
   - Set Limits and Requests for HPA Object to use<br/>
    ```oc set resources dc/$APP_NAME --requests=cpu=10m,memory=80Mi --limits=cpu=20m,memory=120Mi -n $NAMESPACE_DEV```

   - Confirm PodMetrics are available for pod before continuing<br/>
     ```POD_NAME=$(oc get pods -l deploymentconfig=$APP_NAME -n $NAMESPACE_DEV -o name | head -n 1)```<br/>
     ```oc describe PodMetrics $POD_NAME -n $NAMESPACE_DEV```<br/>
  
   - Create Horizontal Pod Autoscaler with 50% Average CPU<br/>
      ```oc autoscale dc/$APP_NAME --max=3 --cpu-percent=50 -n $NAMESPACE_DEV```<br/>
   
   - Send Traffic to Pod to Increase CPU usage and force scaling.<br/>
     ```ROUTE_URL=$(oc get route $APP_NAME -n $NAMESPACE_DEV -o jsonpath='{ .spec.host }')```<br/>
     ```export counter=0 && while :;do curl -X POST "$ROUTE_URL/insert?key=$counter&value=$counter" && eval counter=$(($counter+1));done```

## Vertical Pod Autoscaler
14  **Autoscale Vertically rather than horizontally**<br/>
   - Make sure the VPA Operator is installed. Please see [VPA Operator](https://docs.openshift.com/container-platform/4.5/nodes/pods/nodes-pods-vertical-autoscaler.html)<br/>
   
   - Might be necessary to give Service Account Permission on Namespace<br/>
   ```oc adm policy add-cluster-role-to-user edit system:serviceaccount:openshift-vertical-pod-autoscaler:vpa-recommender -n $NAMESPACE_DEV```
     
   - Create VPA CR for deployment<br/>    
   ```
      echo """
        apiVersion: autoscaling.k8s.io/v1
        kind: VerticalPodAutoscaler
        metadata:
          name: vpa-recommender
        spec:
          targetRef:
            apiVersion: "apps.openshift.io/v1"
            kind:       DeploymentConfig
            name:       $APP_NAME
          updatePolicy:
            updateMode: "Auto" """ | oc create -f - -n $NAMESPACE_DEV
  ```
  <br/>

  - VPA will automatically try to apply changes if it differs significantly from configured resource but we can see VPA recommendation for DeploymentConfig.<br/>
  ```oc get vpa vpa-recommender -n $NAMESPACE_DEV -o json | jq '.status.recommendation'```<br/>   
  
## Monitoring and AutoScaling Application Metrics
15 **Openshift also provides a way for you to use Openshift's platform monitoring to monitor your application metrics and provide alerts on those metrics.Note, this functionality is still in Tech Preview.This only works for applications that expose a /metrics endpoint that can be scraped which this application does. Please visit [Monitoring Your Applications](https://docs.openshift.com/container-platform/4.4/monitoring/monitoring-your-own-services.html) and you can see an example of how to do that [here](https://servicesblog.redhat.com/2020/04/08/application-monitoring-openshift/), before running any of the below steps please enable monitoring using info from the links above**<br/>

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

## Openshift Serverless
16 **Openshift provides serverless functionality via the [Openshift serverless operator](https://docs.openshift.com/container-platform/4.5/serverless/architecture/serverless-serving-architecture.html), Follow steps in documenation to create serveless installation**<br/>

**Create a sample serverless application below and run application**

```
cat << EOF | oc create -f -
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: testflask-serverless
  namespace: $NAMESPACE_DEV
spec:
  template:
    spec:
      containers:
        - image: image-registry.openshift-image-registry.svc:5000/${NAMESPACE_DEV}/${APP_NAME}:latest      
          env:
          - name: APP_CONFIG
            value: "gunicorn.conf.py"
          - name: APP_MODULE
            value: "testapp:app"
          - name: MYSQL_HOST
            value: $MYSQL_HOST
          - name: MYSQL_DATABASE 
            value: $MYSQL_DATABASE
EOF
```
