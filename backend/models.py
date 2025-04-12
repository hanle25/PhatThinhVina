from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'Product'  # Must match the Azure table name exactly

    ProductID = db.Column(db.Integer, primary_key=True)
    ProductName = db.Column(db.String(255), nullable=False)
    ProductDescription = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Product {self.ProductName}>"
    
    def to_dict(self):
        return {
            "ProductID": self.ProductID,
            "ProductName": self.ProductName,
            "ProductDescription": self.ProductDescription,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Storage(db.Model):
    __tablename__ = 'Storage'  # Make sure this matches your Azure table

    StorageID = db.Column(db.Integer, primary_key=True)
    StorageName = db.Column(db.String(255), nullable=False)
    StorageAddress = db.Column(db.String(255), nullable=False)
    StorageLat = db.Column(db.Float, nullable=False)
    StorageLong = db.Column(db.Float, nullable=False)
    StoragePhone = db.Column(db.String(20))  # Optional field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Truck(db.Model):
    __tablename__ = 'Truck'  # Ensure this matches the Azure table name

    TruckID = db.Column(db.Integer, primary_key=True)
    TruckLoad = db.Column(db.Integer, nullable=False)
    TruckPhone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Truck {self.TruckID}>"
    
    def to_dict(self):
        return {
            "TruckID": self.TruckID,
            "TruckLoad": self.TruckLoad,
            "TruckPhone": self.TruckPhone,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Customer(db.Model):
    __tablename__ = 'Customer'  # Must match the Azure table name exactly

    CustomerID = db.Column(db.Integer, primary_key=True)
    CustomerName = db.Column(db.String(255), nullable=False)
    CustomerAddress = db.Column(db.String(255), nullable=False)
    CustomerLong = db.Column(db.Float, nullable=False)
    CustomerLat = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Customer {self.CustomerName}>"
    
    def to_dict(self):
        return {
            "CustomerID": self.CustomerID,
            "CustomerName": self.CustomerName,
            "CustomerAddress": self.CustomerAddress,
            "CustomerLong": self.CustomerLong,
            "CustomerLat": self.CustomerLat,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
