# testFlask

## Test Flask is a simple flask application to show some parts of the Openshift Application Experience for a Python Application.  It's been broken down into a series of modules that cover likely Use Cases  

----------

## Modules

### Module 1: testFlask - Main Application(This Page)

  1. [s2i Build](https://github.com/MoOyeg/testFlask#source-environment-variables)  
  2. [Git Webhooks](https://github.com/MoOyeg/testFlask#webhooks)  
  3. [Openshift Health Checks](https://github.com/MoOyeg/testFlask#health-checks)  
  4. [Horizontal Autoscaling](https://github.com/MoOyeg/testFlask#horizontal-autoscaling-with-cpumemory)  
  5. [Vertical Autoscaling](https://github.com/MoOyeg/testFlask#vertical-pod-autoscaler)  
  6. [User Workload Monitoring](https://github.com/MoOyeg/testFlask#monitoring-and-autoscaling-application-metrics)  
  7. [Serverless Example](https://github.com/MoOyeg/testFlask#openshift-serverless)  
  8. [Async Python Example](https://github.com/MoOyeg/testFlask/tree/quart)  

### Module 2: [Custom s2i Images](https://github.com/MoOyeg/s2i-python-custom.git) - Create Custom s2i Images for Python Applications  

### Module 3: [testFlask-Jenkins](https://github.com/MoOyeg/testFlask-Jenkins) - Create Same Application with a Jenkins Pipeline in Openshift  

### Module 4: [testFlask-Tekton](https://github.com/MoOyeg/testFlask-tekton) - Create Same Application with a Tekton Pipeline in Openshift  

### Module 5: [testFlask-Oauth](https://github.com/MoOyeg/testFlask-Oauth-Proxy) - Application authentication using Openshift Oauth Proxy  

### Module 6: [testflask-gitops](https://github.com/MoOyeg/testflask-gitops) - ArgoCD Application Continous Deployment  

### Module 7: [testflask-helm-repo](https://github.com/MoOyeg/testflask-helm-repo) - Deploy the Same Application via Helm  

### Steps to Run  

### Source Environment Variables

`eval "$(curl https://raw.githubusercontent.com/MoOyeg/testFlask/master/sample_env)"`

1 **Create Necessary Projects**  
```oc new-project $NAMESPACE_DEV```  
```oc new-project $NAMESPACE_PROD```  

2 **This step is Only necessary if you are using a private repo**  
**Create Secret in Openshift for Private/Cluster, example is for github ssh key**  
```oc create secret generic $REPO_SECRET_NAME --type=kubernetes.io/ssh-auth --from-file=ssh-privatekey=$SSHKEY_PATH -n $NAMESPACE_DEV```

 Link Secret with your Service Account,the default Service account for builds is usually builder so will link with builder  
```oc secrets link builder $REPO_SECRET_NAME -n $NAMESPACE_DEV```

3 **Create a New Secret to host our database credentials**  
```oc create secret generic my-secret --from-literal=MYSQL_USER=$MYSQL_USER --from-literal=MYSQL_PASSWORD=$MYSQL_PASSWORD -n $NAMESPACE_DEV```

4 **Create a new mysql instance(Application will use sqlite if no mysql detail is provided)**  
```oc new-app $MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE -l db=mysql -l app=testflask -n $NAMESPACE_DEV```

5 **The new app above will fail because we have not provided the MYSQL user and password,we can provide the database secret to the mysql deployment**  
```oc set env deploy/$MYSQL_HOST --from=secret/my-secret -n $NAMESPACE_DEV```

6 **Create a new application on openshift, using the oc new-app command. With the oc new-app command you have multiple options to specify how you would like to build a running container**.Please see [Openshift Builds](https://docs.openshift.com/container-platform/4.3/builds/understanding-image-builds.html) and [Openshift S2i](https://docs.openshift.com/enterprise/3.2/using_images/s2i_images/python.html),  **Example below uses source-secret created earlier,if you want to use sqlite in the same pod instead of the mysql we created above skip all the database environment variables**  

- If building with DockerFile tag ubi8 image to make it available in cluster  
```oc tag --source=docker registry.redhat.io/ubi8/ubi:latest ubi8:latest -n openshift```


- Private Repo with Source Secret  
```oc new-app python:3.8~git@github.com:MoOyeg/testFlask.git --name=$APP_NAME --source-secret$REPO_SECRET_NAME -l app=testflask --strategy=source  --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app --env=MYSQL_HOST=$MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE -n $NAMESPACE_DEV```  
- Public Repo without Source Secret(s2i Building)  
```oc new-app python:3.8~https://github.com/MoOyeg/testFlask.git --name=$APP_NAME -l app=testflask --strategy=source --env=APP_CONFIG=gunicorn.conf.py --env=APP_MODULE=testapp:app --env=MYSQL_HOST=$MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE -n $NAMESPACE_DEV```  
- Public Repo using the Dockerfile to build(Docker Strategy)  ```oc new-app https://github.com/MoOyeg/testFlask.git --name=$APP_NAME -l app=testflask --env=MYSQL_HOST=$MYSQL_HOST --env=MYSQL_DATABASE=$MYSQL_DATABASE -n $NAMESPACE_DEV```
  
***Patch Environment Details with information from DownWardAPI that our application uses to provide information details***  
```oc patch deploy/$APP_NAME --patch "$(curl https://raw.githubusercontent.com/MoOyeg/testFlask/master/patch-env.json | envsubst)" -n $NAMESPACE_DEV```

7 **Expose the service to the outside world with an openshift route**  
```oc expose svc/$APP_NAME -n $NAMESPACE_DEV```

8 **We can provide your database secret to your app deployment, so your app can use those details**  
```oc set env deploy/$APP_NAME --from=secret/my-secret -n $NAMESPACE_DEV```

9 **You should be able to log into the openshift console now to get a better look at the application, all the commands above can be run in the console, to get more info about the developer console please visit [Openshift Developer Console](https://docs.openshift.com/container-platform/4.4/applications/application_life_cycle_management/odc-creating-applications-using-developer-perspective.html)**

10 **To make the seperate deployments appear as one app in the Developer Console, you can label them. This step does not change app behaviour or performance is a visual aid and would not be required if app was created from developer console**  
```oc label deploy/$APP_NAME app.kubernetes.io/part-of=$APP_NAME -n $NAMESPACE_DEV```  
```oc label deploy/$MYSQL_HOST app.kubernetes.io/part-of=$APP_NAME -n $NAMESPACE_DEV```  
```oc annotate deploy/$APP_NAME app.openshift.io/connects-to=$MYSQL_HOST -n $NAMESPACE_DEV```  

## Webhooks

11 **You can attach a WebHook to your application , so when there is application code change the application is rebuilt to take adavantage of that, you can see steps to this via the developer console .Opensshift will create the html link and secret for you which you can configure in github/gitlab other generic VCS. See more here [Openshift Triggers](https://docs.openshift.com/container-platform/4.4/builds/triggering-builds-build-hooks.html) and see [github webhooks](https://developer.github.com/webhooks/)**  
    -  To get the Webhook Link from the CLI  
       ```oc describe bc/$APP_NAME -n $NAMESPACE_DEV | grep -i -A1 "webhook generic"```  
    -  To get the Webhook Secret from the CLI  
       ```oc get bc/$APP_NAME -n $NAMESPACE_DEV -o jsonpath='{.spec.triggers[*].github.secret}'```  
    - Content Type is application/json and disable ssl verification if your ingress does not have a trusted cert.  

## Health Checks

12 **It is important to be able to provide the status of your application to the platform so the platform does not send requests to application instances not ready or available to recieve them, this can be done with a liveliness and a health probe, please see [Health Checks](https://docs.openshift.com/container-platform/4.4/applications/application-health.html). This application has  sample /health and /ready uri that provide responses about the status of the application**  

- **Create a readiness probe for our application**  
```oc set probe deploy/$APP_NAME --readiness --get-url=http://:8080/ready --initial-delay-seconds=10 -n $NAMESPACE_DEV```  

- **Create a liveliness probe for our application**  
```oc set probe deploy/$APP_NAME --liveness --get-url=http://:8080/health --timeout-seconds=30 --failure-threshold=3 --period-seconds=10 -n $NAMESPACE_DEV```  

- **We can test Openshift Readiness by opening the application page and setting the application ready to down, after a while the application endpoint will be removed from the list of endpoints that recieve traffic for the service,you can confirm by**  
  - ```oc get ep/$APP_NAME -n $NAMESPACE_DEV```  
  - Since the readiness removes the pod endpoint from the service we will not be able to access the app page anymore  
  - We will need to log into the pod to enable the readiness back  
    ```POD_NAME=$(oc get pods -l deploymentconfig=$APP_NAME -n $NAMESPACE_DEV -o name | head -n 1)```  
  - Exec the Pod and curl the pod API to start the pod readiness  
    ```oc exec $POD_NAME curl http://localhost:8080/ready_down?status=up```  

  - **We can test Openshift Liveliness also, when a pod fails it's liveliness check, it is restarted based on the parameters used in the liveliness check, see liveliness probe command above**  
  - Set the Pod's liveliness to down  
    ```POD_NAME=$(oc get pods -l deploymentconfig=$APP_NAME -n $NAMESPACE_DEV -o name | head -n 1)```  
    ```oc exec $POD_NAME curl http://localhost:8080/health_down?status=down```  

## Horizontal AutoScaling with CPU/Memory

13 **Autoscale based on Pod CPU Metrics**  

- Set Limits and Requests for HPA Object to use  
    ```oc set resources deploy/$APP_NAME --requests=cpu=10m,memory=80Mi --limits=cpu=20m,memory=120Mi -n $NAMESPACE_DEV```

- Confirm PodMetrics are available for pod before continuing  
     ```POD_NAME=$(oc get pods -l deploymentconfig=$APP_NAME -n $NAMESPACE_DEV -o name | head -n 1)```  
     ```oc describe PodMetrics $POD_NAME -n $NAMESPACE_DEV```  
  
- Create Horizontal Pod Autoscaler with 50% Average CPU  
      ```oc autoscale deploy/$APP_NAME --max=3 --cpu-percent=50 -n $NAMESPACE_DEV```  

- Send Traffic to Pod to Increase CPU usage and force scaling.  
     ```ROUTE_URL=$(oc get route $APP_NAME -n $NAMESPACE_DEV -o jsonpath='{ .spec.host }')```  
     ```export counter=0 && while :;do curl -X POST "$ROUTE_URL/insert?key=$counter&value=$counter" && eval counter=$(($counter+1));done```

## Vertical Pod Autoscaler

14  **Autoscale Vertically rather than horizontally**  

- Make sure the VPA Operator is installed. Please see [VPA Operator](https://docs.openshift.com/container-platform/4.5/nodes/pods/nodes-pods-vertical-autoscaler.html)  

  - Might be necessary to give Service Account Permission on Namespace  
   ```oc adm policy add-cluster-role-to-user edit system:serviceaccount:openshift-vertical-pod-autoscaler:vpa-recommender -n $NAMESPACE_DEV```

  - Create VPA CR for deployment

   ```bash
      echo """
        apiVersion: autoscaling.k8s.io/v1
        kind: VerticalPodAutoscaler
        metadata:
          name: vpa-recommender
        spec:
          targetRef:
            apiVersion: "apps.openshift.io/v1"
            kind:       Deployment
            name:       $APP_NAME
          updatePolicy:
            updateMode: "Auto" """ | oc create -f - -n $NAMESPACE_DEV
  ```

  - VPA will automatically try to apply changes if it differs significantly from configured resource but we can see VPA recommendation for DeploymentConfig.  
  ```oc get vpa vpa-recommender -n $NAMESPACE_DEV -o json | jq '.status.recommendation'```  
  
## Monitoring and AutoScaling Application Metrics

15 **Openshift also provides a way for you to use Openshift's platform monitoring to monitor your application metrics and provide alerts on those metrics.Note, this functionality is still in Tech Preview.This only works for applications that expose a /metrics endpoint that can be scraped which this application does. Please visit [Monitoring Your Applications](https://docs.openshift.com/container-platform/4.10/monitoring/enabling-monitoring-for-user-defined-projects.html) and you can see an example of how to do that [here](https://servicesblog.redhat.com/2020/04/08/application-monitoring-openshift/), before running any of the below steps please enable monitoring using info from the links above**  

- **Create a servicemonitor using below code (Please enable cluster monitoring with info from above first), servicemonitor label must match label specified from the deployment above.**  

```bash
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
  
- **After the servicemonitor is created we can confirm by looking up the application metrics under monitoring-->metrics, one of the metrics exposed is Available_Keys(Type Available_Keys in query and run) so as more keys are added on the application webpage we should see this metric increase**

- **We can also create alerts based on Application Metrics using the Openshift's Platform AlertManager via Prometheus,[Openshift Alerting](https://docs.openshift.com/container-platform/4.8/monitoring/managing-alerts.html).We need to create an Alerting Rule to recieve Alerts**

```bash
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

- **The above alert should only fire when we have more than 4 keys in the application, go to the application webpage and add more than 4 keys to the DB, we should get an alert when we go to Monitoring-Alerts-AlertManager UI(Top of Page)**

## Openshift Serverless

16 **Openshift provides serverless functionality via the [Openshift serverless operator](https://docs.openshift.com/container-platform/4.5/serverless/architecture/serverless-serving-architecture.html), Follow steps in documenation to create serveless installation**  

- **Create a sample serverless application below and run application**

```bash
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

## ASGI/Quart/Uvicorn

17 **Build and Alternate version of the testflask application using ASGI and Uvicorn**

- Build custom builder image of uvicorn(Sample provided)  
     ```oc new-build https://github.com/MoOyeg/s2i-python-custom.git --name=s2i-ubi8-uvicorn --context-dir=s2i-ubi8-uvicorn -n $NAMESPACE_DEV```

- Build Application Image using previous image with custom gunicorn worker  
     ```oc new-app s2i-ubi8-uvicorn~https://github.com/MoOyeg/testFlask.git#quart --name=testquart -l app=testquart --strategy=source --env=APP_CONFIG=gunicorn-uvi.conf --env=APP_MODULE=testapp:app --env CUSTOM_WORKER="true" -n $NAMESPACE_DEV```


test
