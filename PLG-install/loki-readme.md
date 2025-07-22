sudo mkdir /etc/loki

ls
cd /
cd etc/loki
sudo wget -qO loki.gz "https://github.com/grafana/loki/releases/download/v3.5.0/loki-linux-amd64.zip"
sudo gunzip loki.gz 
sudo chmod a+x loki 
sudo ln loki /usr/local/bin/loki
sudo wget -qO loki-local-config.yaml "https://raw.githubusercontent.com/grafana/loki/v3.5.0/cmd/loki/loki-local-config.yaml"
loki -version
cd
create loki.service at location /etc/systemd/system/loki.service
`sudo vi /etc/systemd/system/loki.service`

sudo service start loki
sudo service loki start
systemctl enable loki
sudo passwd ubuntu
systemctl enable loki
systemctl status loki
systemctl daemon-reload

##Trobleshoot loki service failure
`loki -config.file=loki-local-config.yaml`  
