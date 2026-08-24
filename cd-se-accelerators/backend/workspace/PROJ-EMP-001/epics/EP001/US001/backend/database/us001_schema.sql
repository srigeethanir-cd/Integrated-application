python
# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create a database engine
engine = create_engine('postgresql://user:password@localhost/dbname')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the Component class
class Component(Base):
    __tablename__ = 'components'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

    def __repr__(self):
        return f"Component(id={self.id}, name='{self.name}', description='{self.description}')"

# Create all tables in the engine
Base.metadata.create_all(engine)

# Create a new session
session = Session()

# Create a new component
def create_component(name, description):
    new_component = Component(name=name, description=description)
    session.add(new_component)
    session.commit()
    return new_component

# Get all components
def get_all_components():
    return session.query(Component).all()

# Get a component by id
def get_component_by_id(id):
    return session.query(Component).filter_by(id=id).first()

# Update a component
def update_component(id, name, description):
    component = get_component_by_id(id)
    if component:
        component.name = name
        component.description = description
        session.commit()
    return component

# Delete a component
def delete_component(id):
    component = get_component_by_id(id)
    if component:
        session.delete(component)
        session.commit()
    return component