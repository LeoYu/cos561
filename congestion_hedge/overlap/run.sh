 
sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  tree.topo default.req 20 -1 0.00015 1600

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  tree.topo default.req 20 0 0.00015 1600

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  tree.topo default.req 20 1 0.00015 1600

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  tree.topo default.req 20 2 0.00015	1600

sudo rm *.kill *.txt
sudo  mn -c
