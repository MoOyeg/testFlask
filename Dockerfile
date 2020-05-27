FROM centos:7

# Install the required software
RUN yum update -y && yum -y install python3 && \
yum install -y mysql-devel gcc gcc-devel python-devel && \
# clean yum cache files, as they are not needed and will only make the image bigger in the end
yum clean all -y 

#Copy all code to image
COPY ./* /

#Get pip install
RUN curl -O https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py

#Install Requirements
RUN pip install -r requirements.txt

