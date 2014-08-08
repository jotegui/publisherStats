import Lumper as L
import CartoDBObject as cdb
import GoogleStorageObject as gso
import ModelContainer as mc

from imp import reload

l = L.Lumper()

c1 = cdb.CartoDBObject(l[0])
g1 = gso.GoogleStorageObject.fromuri(c1.download)
m = mc.ModelContainer()
m.parse_gso(g1)

c2 = cdb.CartoDBObject(l[3])
g2 = gso.GoogleStorageObject.fromuri(c2.download)
m.parse_gso(g2)

