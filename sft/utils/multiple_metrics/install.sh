sudo apt-get update
#install c-sharp environment
sudo apt-get install mono-runtime mono-complete -y
#install php
sudo apt-get install php -y
#install javascript
#sudo apt-get install nodejs -y
#install typescript
mkdir -p /usr/lib/npm/
tar -xzf zips/node-v16.14.0-linux-x64.tar.gz -C /usr/lib/npm/
export PATH=$PATH:/usr/lib/npm/node-v16.14.0-linux-x64/bin/
npm install -g typescript
#install java
mkdir -p /usr/lib/jvm
sudo tar -xzf zips/openlogic-openjdk-8u412-b08-linux-x64.tar.gz -C /usr/lib/jvm
export JAVA_HOME=/usr/lib/jvm/openlogic-openjdk-8u412-b08-linux-x64
export PATH=$JAVA_HOME/bin:$PATH
#c++
#sudo apt-get install libboost-all-dev -y
cd zips/boost_1_76_0
./bootstrap.sh --prefix=/usr/local
sudo ./b2 install
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH