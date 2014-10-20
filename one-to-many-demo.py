from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
 
from sqlalchemy.orm import sessionmaker
 
import pdb   
import logging
log = logging.getLogger(__name__)
 
################################################################################
# set up logging - see: https://docs.python.org/2/howto/logging.html
 
# when we get to using Flask, this will all be done for us
import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)
 
 
################################################################################
# Domain Model
 
Base = declarative_base()
log.info("base class generated: {}".format(Base) )
 
# define our domain model
class Species(Base):
    """
    domain model class for a Species
    """
    __tablename__ = 'species'
 
    # database fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    breeds = relationship('Breed', backref="species")
 
    # methods
    def __repr__(self):
        return self.name                   
 
 
class Breed(Base):
    """
    domain model class for a Breed
    many-breeds-to-one-species
    """
    __tablename__ = 'breed'
 
    # database fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    species_id = Column(Integer, ForeignKey('species.id'), nullable=False) 
    pets = relationship('Pet', backref="breed")
          
    # methods
    def __repr__(self):
        return "{}: {}".format(self.name, self.species) 

class Pet(Base):
    """
    domain model class for Pet
    many-pets-to-one-breed 
    """
    __tablename__ = 'pet'

    #database fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    adopted = Column(Boolean, nullable=False)
    breed_id = Column(Integer, ForeignKey('breed.id'), nullable=True) 
    shelter_id = Column(Integer, ForeignKey('shelter.id'))

class Shelter(Base):
    """
    domain model class for Shelter
    one-shelter-to-many-pets
    """
    __tablename__ = 'shelter'

    #database fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    website = Column(String)
    shelters = relationship('Pet', backref="shelter")

 
 
################################################################################
def init_db(engine):
    "initialize our database, drops and creates our tables"
    log.info("init_db() engine: {}".format(engine) )
    
    # drop all tables and recreate
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
 
    log.info("  - tables dropped and created")
 
 
 
if __name__ == "__main__":
    log.info("main executing:")              
 
    # create an engine
    # TODO: allow passing in a db connection string from a command line arg
    engine = create_engine('sqlite:///:memory:')
    log.info("created engine: {}".format(engine) )
 
    # if we asked to init the db from the command line, do so
    if True:
        init_db(engine)
 
    # call the sessionmaker factory to make a Session class 
    Session = sessionmaker(bind=engine)
    
    # get a local session for the this script
    db_session = Session()
    log.info("Session created: {}".format(db_session) )
   
    # count our starting species & breeds
    num_species = db_session.query(Species).count()
    num_breeds = db_session.query(Breed).count()
    log.info("starting with {} species and {} breeds".format(num_species, num_breeds) )
 
    log.info("Creating Species: Cat and Dog (Transient)")
    cat = Species(name="Cat")
    dog = Species(name="Dog")
    
    # we can verify that cat and dog do not have ids yet.
    assert cat.id == None
    assert dog.id == None
    log.info("Type of cat.id is {}. Type of dog.id is {}".format(type(cat.id), type(dog.id) ))
 
 
    # add them to the session and commit to save to db
    log.info("Adding dog and cat to session and committing.")    
    db_session.add_all( [cat, dog] )
    db_session.commit()
 
    # now they have ids
    assert cat.id != None
    assert dog.id != None
    log.info("Now the type of cat.id is {} and type of dog.id is {}".format(type(cat.id), type(dog.id) ))
 
    # let's use that id to make a breed
    log.info("Creating three new dog breeds: Poodle, Labrador Retriever, and Golden Retriever")
    poodle = Breed(name='Poodle', species_id=dog.id)
    lab = Breed(name='Labrador Retriever', species_id=dog.id)
    golden = Breed(name='Golden Retriever', species_id=dog.id)
 
    # dog.breeds is still empty, as we have saved the above
    log.info("New breeds created, but still transient. There are {} dog breeds in the database".format(
        len(dog.breeds)))
    assert dog.breeds == []
    db_session.add_all( [poodle, lab, golden] )
    db_session.commit()
 
    # now dog.breeds contains lab, poodle, & golden
    # we can use set to assert on membership disregarding order in list
    assert set( [poodle,lab,golden] ) == set( dog.breeds )
    log.info("New breeds saved. There are now {} dog breeds in the database".format(
        len(dog.breeds)))
   
    # Now let's see how SQLAlchemy let's us assign objects as foreign keys even if those
    # objects have not yet been saved.  
 
    # Let's make a new species, parrot and a new breed, Norwegian Blue.
    # But instead of building our relationship with the 'species_id' field,
    # we will use the 'species' relationship. We can use the species parrot, 
    # even though it has no ID and has not yet been persisted. 
    # SQLAlchemy's Identity Map can manage all of this
 
    log.info("/n/n/Demonstrating the smarts of the Identity Map")
    log.info("There are currently {} parrot species in the db".format(
        db_session.query(Species).filter(Species.name=='Parrot').count() ) )
    log.info("Creating new breed, Norwegian Blue, which is of the Parrot Species")
    norwegian_blue = Breed(name="Norwegian Blue",
        species=Species(name="Parrot")  )
    parrot = norwegian_blue.species
    
    log.info("Type of parrot.id is {} and norwegian_blue.id is {}".format(
        type(parrot.id), type(norwegian_blue.id) ) )
    log.info("But norwegian_blue.species is: {}".format(norwegian_blue.species))
    log.info("And parrot.breeds is {}".format(parrot.breeds))
    assert norwegian_blue.species == parrot
    assert norwegian_blue in parrot.breeds 
 
    log.info('Now lets add parrot to the session and commit, and we\'ll get' +\
        ' our new breeds for free.')
    log.info('adding and committing parrot to session') 
    db_session.add(parrot)
    db_session.commit()
 
    log.info("Now parrot.id is {} and norwegian_blue.id is {}".format(
        parrot.id, norwegian_blue.id))    



    # Time to add new shelters
    log.info("There are currently {} shelters in the db".format(db_session.query(Shelter).count()))
    log.info("Adding two new shelters to the db (Transient)")
    nycpet = Shelter(name="NYC Pet Orphanage", website="http://www.nyc-pet-orphanage.com")
    nola = Shelter(name="New Orleans Pet Hotel", website="http://www.neworleanspethotel.com")

    # we can verify that nycpet and nola shelters do not have ids yet.
    assert nycpet.id == None
    assert nola.id == None
    log.info("Type of nycpet.id is {}. Type of nola.id is {}".format(type(nycpet.id), type(nola.id) ))

    # add them to the session and commit to save to db
    log.info("Adding nycpet and nola to session and committing.")    
    db_session.add_all( [nycpet, nola] )
    db_session.commit()
 
    # now they have ids
    assert nycpet.id != None
    assert nola.id != None
    log.info("Now the type of nycpet.id is {} and type of nola.id is {}".format(type(nycpet.id), type(nola.id) ))

    
    # Adding two new pets
    log.info("There are currently {} pets in the db".format(db_session.query(Pet).count()))
    log.info("Adding two new pets to the db")
## How would I pull in the foreign key for something that I didn't add to the db in this file? 
## I use nycpet and golden to call those specific object's ids.. but what if this is file 2?
    thomas = Pet(name="Thomas", age=5, adopted=0, shelter_id=nycpet.id, breed_id=golden.id)
    sue = Pet(name="Sue", age=8, adopted=1, breed_id=poodle.id)

    # we can verify that thomas and sue do not have ids yet.
    assert thomas.id == None
    assert sue.id == None
    log.info("Type of thomas.id is {}. Type of sue.id is {}".format(type(thomas.id), type(sue.id) ))

    # add them to the session and commit to save to db
    log.info("Adding thomas and sue to session and committing.")    
    db_session.add_all( [thomas, sue] )
    db_session.commit()
 
    # now they have ids
    assert thomas.id != None
    assert sue.id != None
    log.info("Now the type of thomas.id is {} and type of sue.id is {}".format(type(thomas.id), type(sue.id) ))

    
    ## Print out the final status of our db
    
    num_pets = db_session.query(Pet).count()
    num_breeds = db_session.query(Breed).count()
    num_species = db_session.query(Species).count()
    num_shelters = db_session.query(Shelter).count()
    log.info('We now have {} pets, {} breeds, {} species, and {} shelters stored in our database'.format(num_pets, num_breeds, num_species, num_shelters))
  



    db_session.close()
    log.info("all done!")