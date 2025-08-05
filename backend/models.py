from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

class Products(db.Model):
    __tablename__ = 'Products'

    ProductID = db.Column(
        db.String(6), primary_key=True,
        server_default=text("'P' || LPAD(NEXTVAL('\"IDseq6Fig\"')::TEXT, 5, '0')")
    )
    ProductName = db.Column(db.String(255), nullable=False)
    ProductDescription = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Product {self.ProductName}>"

    def to_dict(self):
        return {
            "ProductID": self.ProductID,
            "ProductName": self.ProductName,
            "ProductDescription": self.ProductDescription,
        }

class Catalogs(db.Model):
    __tablename__ = 'Catalogs'

    CatalogID = db.Column(
        db.String(3), primary_key=True,
        server_default=text("'C' || LPAD(NEXTVAL('\"IDseq3Fig\"')::TEXT, 2, '0')")
    )
    CatalogName = db.Column(db.String(255), nullable=False)
    SpaceEquivalent = db.Column(db.Float, nullable=False)
    Num = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Catalog {self.CatalogName}>"

    def to_dict(self):
        return {
            "CatalogID": self.CatalogID,
            "CatalogName": self.CatalogName,
            "SpaceEquivalent": self.SpaceEquivalent,
            "Num": self.Num,
        }

class Storages(db.Model):
    __tablename__ = 'Storages'

    StorageID = db.Column(
        db.String(3), primary_key=True,
        server_default=text("'S' || LPAD(NEXTVAL('\"IDseq3Fig\"')::TEXT, 2, '0')")
    )
    StorageName = db.Column(db.String(255), nullable=False)
    StorageAddress = db.Column(db.String(255), nullable=False)
    StorageLat = db.Column(db.Float, nullable=False)
    StorageLong = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Storage {self.StorageName}>"

    def to_dict(self):
        return {
            "StorageID": self.StorageID,
            "StorageName": self.StorageName,
            "StorageAddress": self.StorageAddress,
            "StorageLat": self.StorageLat,
            "StorageLong": self.StorageLong,
        }
class Vehicles(db.Model):
    __tablename__ = 'Vehicles'

    VehicleID = db.Column(
        db.String(6), primary_key=True,
        server_default=text("'V' || LPAD(NEXTVAL('\"IDseq6Fig\"')::TEXT, 5, '0')")
    )
    VehicleType = db.Column(db.String(255), nullable=False)
    VehicleCapacity = db.Column(db.Float, nullable=True)
    VehicleCurrentLoad = db.Column(db.Float, nullable=True)
    VehicleLat = db.Column(db.Float, nullable=False)
    VehicleLong = db.Column(db.Float, nullable=False)
    VehicleContract = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f"<Vehicle {self.VehicleID}>"

    def to_dict(self):
        return {
            "VehicleID": self.VehicleID,
            "VehicleType": self.VehicleType,
            "VehicleCapacity": self.VehicleCapacity,
            "VehicleCurrentLoad": self.VehicleCurrentLoad,
            "VehicleLat": self.VehicleLat,
            "VehicleLong": self.VehicleLong,
            "VehicleContract": self.VehicleContract,
        }

class Customers(db.Model):
    __tablename__ = 'Customers'

    CustomerID = db.Column(
        db.String(6), primary_key=True,
        server_default=text("'C' || LPAD(NEXTVAL('\"IDseq6Fig\"')::TEXT, 5, '0')")
    )
    CustomerName = db.Column(db.String(255), nullable=False)
    CustomerAddress = db.Column(db.String(255), nullable=False)
    CustomerLong = db.Column(db.Float, nullable=False)
    CustomerLat = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Customer {self.CustomerName}>"

    def to_dict(self):
        return {
            "CustomerID": self.CustomerID,
            "CustomerName": self.CustomerName,
            "CustomerAddress": self.CustomerAddress,
            "CustomerLong": self.CustomerLong,
            "CustomerLat": self.CustomerLat,
        }

class VehicleCustomer(db.Model):
    __tablename__ = 'VehicleCustomer'

    VehicleID = db.Column(db.String(6), db.ForeignKey('Vehicles.VehicleID'), primary_key=True)
    CustomerID = db.Column(db.String(6), db.ForeignKey('Customers.CustomerID'), primary_key=True)
    StorageID = db.Column(db.String(3), db.ForeignKey('Storages.StorageID'), primary_key=True)
    LoadWeight = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<VehicleCustomer {self.VehicleID} -> {self.CustomerID} (Storage: {self.StorageID})>"

    def to_dict(self):
        return {
            "VehicleID": self.VehicleID,
            "CustomerID": self.CustomerID,
            "StorageID": self.StorageID,
            "LoadWeight": self.LoadWeight,
        }
