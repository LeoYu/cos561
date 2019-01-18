 
sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 13 -1 0.00005 4000

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 13 0 0.00005 4000

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 13 1 0.00005 4000

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 13 2 0.00005	4000

sudo rm *.kill *.txt
sudo  mn -c
