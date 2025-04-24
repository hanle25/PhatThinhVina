from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Products(db.Model):
    __tablename__ = 'Products'  # Must match the Azure table name exactly

    ProductID = db.Column(db.String(6), primary_key=True)
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

class Storages(db.Model):
    __tablename__ = 'Storages'  # Make sure this matches your Azure table

    StorageID = db.Column(db.String(3), primary_key=True)
    StorageName = db.Column(db.String(255), nullable=False)
    StorageAddress = db.Column(db.String(255), nullable=False)
    StorageLat = db.Column(db.Float, nullable=False)
    StorageLong = db.Column(db.Float, nullable=False)
    StoragePhone = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f"<Storage {self.StorageName}>"
    
    def to_dict(self):
        return {
            "StorageID": self.StorageID,
            "StorageName": self.StorageName,
            "StorageAddress": self.StorageAddress,
            "StorageLat": self.StorageLat,
            "StorageLong": self.StorageLong,
            "StoragePhone": self.StoragePhone,
        }

class Trucks(db.Model):
    __tablename__ = 'Trucks'  # Ensure this matches the Azure table name

    TruckID = db.Column(db.String(3), primary_key=True)
    TruckLoad = db.Column(db.Integer, nullable=False)
    TruckPhone = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f"<Truck {self.TruckID}>"
    
    def to_dict(self):
        return {
            "TruckID": self.TruckID,
            "TruckLoad": self.TruckLoad,
            "TruckPhone": self.TruckPhone,
        }

class Customers(db.Model):
    __tablename__ = 'Customers'  # Must match the Azure table name exactly

    CustomerID = db.Column(db.String(6), primary_key=True)
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
