from app.db.session import engine, Base
from app.models.user import User
from app.models.kst import KSTLocation
from app.models.category import KSTCategory
from app.models.theme import KSTThemeRiset
from app.models.facility import KSTFacility
from app.models.collaboration import KSTCollaboration
from app.models.dampak import KSTDampak
from app.models.wilayah import WilayahProvince, WilayahRegency

Base.metadata.create_all(bind=engine)
print("Tables created.")
