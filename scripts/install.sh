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

install_elastic(){
    cd $BASE_PATH
    
    wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ELK_VERSION}.tar.gz
    tar -zxf elasticsearch-${ELK_VERSION}.tar.gz
    cd elasticsearch-${ELK_VERSION}
    nohup bin/elasticsearch &
    cd -
}


install_kibana(){
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
}


install_logstash(){
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
}

install_kafka(){
# Install Kafka
    cd $BASE_PATH
    wget http://apache.claz.org/kafka/${KAFKA_VERSION}/kafka_2.11-${KAFKA_VERSION}.tgz
    tar -zxf kafka_2.11-${KAFKA_VERSION}.tgz
    cd kafka_2.11-${KAFKA_VERSION}
    nohup bin/zookeeper-server-start.sh config/zookeeper.properties &
    sleep 60
    nohup bin/kafka-server-start.sh config/server.properties &
    sleep 60
}

install(){
    install_elastic
    install_kibana
    install_logstash
    install_kafka
}

restart(){
    for i in `ps -ef|grep -E 'elasticsearch|zookeeper|kafka-server|logstash|kibana'|grep -v grep |awk '{print $2}'`; do kill -9 $i; done

    echo "Starting Elastic"
    nohup $BASE_PATH/elasticsearch-${ELK_VERSION}/bin/elasticsearch &
    sleep 30

    if [ `uname -v |grep -ic darwin` -gt 0 ]; then
        distro=darwin
    else
        distro=linux
    fi
    echo "Starting kibana"
    nohup $BASE_PATH/kibana-${ELK_VERSION}-$distro-x86_64/bin/kibana &
    sleep 30

    echo "Starting logstash"
    nohup $BASE_PATH/logstash-${ELK_VERSION}/bin/logstash -f config/logstash.conf &
    sleep 10

    echo "Starting kafka"
    nohup $BASE_PATH/kafka_2.11-${KAFKA_VERSION}/bin/zookeeper-server-start.sh config/zookeeper.properties &
    sleep 10
    nohup $BASE_PATH/kafka_2.11-${KAFKA_VERSION}/bin/kafka-server-start.sh config/server.properties &

    echo "All done"
}

main(){
    if [ "$1" == "restart" ]; then
        restart
    else
	install
    fi
}

main $*
echo "All done"
