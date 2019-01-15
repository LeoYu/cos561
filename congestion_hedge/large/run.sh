 
sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 5 -1 0.0002

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 5 0 0.0002

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 5 1 0.0002

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 5 2 0.0002

sudo rm *.kill *.txt
sudo  mn -c
