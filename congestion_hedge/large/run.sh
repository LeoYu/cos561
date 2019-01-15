 
sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 5 -1 0.00005 4000

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 5 0 0.00005 4000

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 5 1 0.00005 4000

sudo rm *.kill *.txt
sudo  mn -c
sudo python ../build.py  large.topo default.req 5 2 0.00005	4000

sudo rm *.kill *.txt
sudo  mn -c
