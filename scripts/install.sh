#!/bin/bash

# Simple toy script for single node - Kafka + ELK

# Written for Ubuntu

# Install Java if it does not exist

if [ -z $JAVA_HOME ]; then
    sudo apt-get install default-jre -y
    if [ $? -eq 0 ]; then
	echo 'export JAVA_HOME=/usr/lib/jvm/default-java' >> ~/.profile
	echo 'export PATH=$PATH:$JAVA_HOME' >> ~/.profile
    fi 
fi

# Install Elasticsearch

BASE_PATH=$HOME
ELK_VERSION=6.2.2
KAFKA_VERSION=1.0.1

cd $BASE_PATH

wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ELK_VERSION}.tar.gz
tar -zxf elasticsearch-${ELK_VERSION}.tar.gz
cd elasticsearch-${ELK_VERSION}
nohup bin/elasticsearch &
cd -


# Install Kibana
cd $BASE_PATH
if [ `uname -v |grep -ic darwin` -gt 0 ]; then
    distro=darwin
else
    distro=linux
fi
wget https://artifacts.elastic.co/downloads/kibana/kibana-${ELK_VERSION}-$distro-x86_64.tar.gz
tar -zxf kibana-${ELK_VERSION}-$distro-x86_64.tar.gz
cd kibana-${ELK_VERSION}-$distro-x86_64
perl -pi -e 's/#server.port: 5601/server.port: 5601/g' config/kibana.yml
perl -pi -e 's/#server.host: "0.0.0.0"/server.host: "0.0.0.0"/g' config/kibana.yml
perl -pi -e 's/#server.host: "localhost"/server.host: "0.0.0.0"/g' config/kibana.yml
nohup bin/kibana &

# Install Logstash
cd $BASE_PATH
wget https://artifacts.elastic.co/downloads/logstash/logstash-${ELK_VERSION}.tar.gz
tar -zxf logstash-${ELK_VERSION}.tar.gz
cd logstash-${ELK_VERSION}
echo '
input {
    kafka {
        codec => json
    }
}
output {
    elasticsearch { hosts => ["localhost:9200"] }
    stdout { codec => rubydebug }
}
' > config/logstash.conf
nohup bin/logstash -f config/logstash.conf &
echo "Started Logstash"

# Install Kafka
cd $BASE_PATH
wget http://apache.claz.org/kafka/${KAFKA_VERSION}/kafka_2.11-${KAFKA_VERSION}.tgz
tar -zxf kafka_2.11-${KAFKA_VERSION}.tgz
cd kafka_2.11-${KAFKA_VERSION}
nohup bin/zookeeper-server-start.sh config/zookeeper.properties &
nohup bin/kafka-server-start.sh config/server.properties &
sleep 60

echo "All done"
