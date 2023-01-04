from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from datetime import datetime, time

from database import Base

class Sales(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True) 
    market = Column(String)
    product_line = Column(String)
    brand = Column(String)
    sub_brand = Column(String)
    component = Column(String)
    sku = Column(String)
    sku_desc = Column(String)
    cost = Column(Float)
    asp=Column(Float)
    margin=Column(Float)
    y_2017 = Column(Float)
    y_2018 = Column(Float)
    y_2019 = Column(Float)
    y_2020 = Column(Float)
    y_2021 = Column(Float)
    y_2022 = Column(Float)
    y_2023 = Column(Float)
    y_2024 = Column(Float)
    y_2025 = Column(Float)
    y_2026 = Column(Float)
    y_2027 = Column(Float)
    y_2028 = Column(Float)
    y_2029 = Column(Float)
    y_2030 = Column(Float)


class Audit(Base):
    __tablename__ = "audit"
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("sales.id"))
    field_name = Column(String, index=True)
    old_value = Column(Float)
    new_value = Column(Float)
    changed_on = Column(String)