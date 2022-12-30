#Tag ubi8 image to make it available in cluster -- oc tag --source=docker registry.redhat.io/ubi8/ubi:latest ubi8:latest -n openshift
FROM image-registry.openshift-image-registry.svc:5000/openshift/ubi8
#FROM registry.redhat.io/ubi8/ubi:latest

#ENV Variables
ENV APP_MODULE testapp:app
ENV APP_CONFIG gunicorn.conf.py

# Install the required software
RUN yum update -y && yum install git python38 -y

# Install pip
#RUN curl -O https://bootstrap.pypa.io/pip/3.6/get-pip.py && python3 get-pip.py && python3 get-pip.py

#Make Application Directory
RUN mkdir ./app && cd ./app

# Copy Files into containers
COPY ./ ./app

#WORKDIR
WORKDIR ./app

# Install App Dependecies
RUN pip3.8 install -r requirements.txt

#Expose Ports
EXPOSE 8080/tcp

#Change Permissions to allow not root-user work
RUN chmod -R g+rw ./

#Change User
USER 1001

#ENTRY
ENTRYPOINT gunicorn -c $APP_CONFIG $APP_MODULE
