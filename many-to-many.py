from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table
from sqlalchemy.schema import UniqueConstraint
 
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
    has a with many-to-one relationship Species
    """
    __tablename__ = 'breed'
 
    # database fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    species_id = Column(Integer, ForeignKey('species.id'), nullable=False )            
    pets = relationship('Pet', backref="breed")
    # methods
    def __repr__(self):
        return "{}: {}".format(self.name, self.species) 
 
 
    # Build associative table and BreedTrait class

breed_breedtrait_table = Table('breed_breedtrait', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('breed_id', Integer, ForeignKey('breed.id'), nullable=False),
    Column('breedtrait_id', Integer, ForeignKey('breedtrait.id'), nullable=False)
)

class BreedTrait(Base):
    """
    many-to-many relationship with breeds
    """
    __tablename__ = 'breedtrait'

    #database fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    breed = relationship('Breed', secondary=breed_breedtrait_table, backref='breedtrait')

    def __repr__(self):
        return "Trait: {}".format(self.trait)
 
class Shelter(Base):
    __tablename__ = 'shelter'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    website = Column(Text)
    pets = relationship('Pet', backref="shelter")
 
    def __repr__(self):
        return "Shelter: {}".format(self.name) 

class PetPersonAssociation(Base):
    __tablename__ = 'petPersonAssociation'
    __table_args__ = (
            UniqueConstraint('pet_id', 'person_id', name='person_pet_uniqueness_constraint'),
        )


    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey('pet.id'), nullable=False)
    person_id = Column(Integer, ForeignKey('person.id'), nullable=False)
    nickname = Column(String)

    pet = relationship('Pet', backref=backref('person_associations'))
    person = relationship('Person', backref=backref('pet_associations'))

    def __repr__(self):
        return "PetPersonAssociation( {} : {} )".format(self.pet.name, 
            self.person.first_name)
 
 
# If we went the many-to-many association table route, this is what we'd use:
# pet_person_table = Table('pet_person', Base.metadata,
#     Column('pet_id', Integer, ForeignKey('pet.id'), nullable=False),
#     Column('person_id', Integer, ForeignKey('person.id'), nullable=False),
#     Column('nickname', String)
# )
 


pet_to_pet = Table("pet_to_pet", Base.metadata,
    Column("left_pet_id", Integer, ForeignKey("pet.id"), primary_key=True),
    Column("right_pet_id", Integer, ForeignKey("pet.id"), primary_key=True)
)

 
class Pet(Base):
    """
    domain model class for a Pet, which has a many-to-one relation with Shelter, 
    a many-to-one relation with breed, and a many-to-many relation with person
    """
    """Each pet can have 2 parents and 0 or more children """
    __tablename__ = 'pet'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    adopted = Column(Boolean)
    breed_id = Column(Integer, ForeignKey('breed.id'), nullable=False ) 
    shelter_id = Column(Integer, ForeignKey('shelter.id') ) 
    #parentM_id = Column(Integer, ForeignKey('pet.id'), nullable=True)
    right_pet_id = Column(Integer, ForeignKey('pet.id'), nullable=True)
    left_pet_id = Column(Integer, ForeignKey('pet.id'), nullable=True)
    #parentM = relationship('Pet', remote_side='Pet.id', backref="children")
    right_nodes = relationship("Pet", secondary=pet_to_pet, primaryjoin=id==pet_to_pet.c.left_pet_id, secondaryjoin=id==pet_to_pet.c.right_pet_id,backref="left_pets")



    def nicknames(self):
        """return all nicknames for this pet"""
        return [ assoc.nickname for assoc in self.person_associations]

    def __repr__(self):
        return "Pet:{}".format(self.name) 
 
class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    age = Column(Integer)
    _phone = Column(String)

 
    @property
    def phone(self):
        """return phone number formatted with hyphens"""
        # get the phone number from the database, mapped to private self._phone
        num = self._phone
        # return a formatted version using hyphens
        return "%s-%s-%s" % (num[0:3], num[3:6], num[6:10])
 
    # phone number writing property, writing to public Person.phone calls this 
    @phone.setter 
    def phone(self, value):
        """store only numeric digits, raise exception on wrong number length"""
        # remove any hyphens
        number = value.replace('-', '')
        # remove any spaces
        number = number.replace(' ', '')
        # check length, raise exception if bad
        if len(number) != 10:
            raise Exception("Phone number not 10 digits long")
        else:
            # write the value to the property that automatically goes to DB
            self._phone = number
 
    def __repr__(self):
        return "Person: {} {}".format(self.first_name, self.last_name) 
 
 
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
   
 
    # create two people: Tom and Sue
    log.info("Creating person object for Tom")
    tom = Person(first_name="Tom",
                last_name="Smith",
                age=52,
                phone = '555-555-5555')
 
    log.info("Creating person object for Sue")
    sue = Person(first_name="Sue",
                last_name="Johson",
                age=54,
                phone = '555 243 9988')
 
 
    # create two animals, and in process, new species, with two breeds.
    # Note how we only explicitly commit spot and goldie below, but by doing so
    # we also save our new people, breeds, and species.
 
    log.info("Creating pet object for Spot, who is a Dalmatian dog")
    spot = Pet(name = "Spot",
                age = 2,
                adopted = True,
                breed = Breed(name="Dalmatian", species=Species(name="Dog"))
                )
 
    # now we set Spot's breed to a variable because we don't want to create
    # a duplicate record for Dog in the species table, which is what would 
    # happen if we created Dog on the fly again when instantiating Goldie
    dog = spot.breed.species
 
    log.info("Creating pet object for Goldie, who is a Golden Retriever dog")
    goldie = Pet(name="Goldie",
                age=9,
                adopted = False,
                shelter = Shelter(name="Happy Animal Place"),
                breed = Breed(name="Golden Retriever", species=dog)
                ) 
 
    log.info("Adding Goldie and Spot to session and committing changes to DB")


    db_session.add_all([spot, goldie, tom, sue])
    db_session.commit()

 
    # Now we add breed traits to golden retrievers and dalmations

    golden = goldie.breed
    dalm = spot.breed

    log.info("Creating breed trait for breed golden")
    longhair = BreedTrait(name="Fluffy", breed=[golden])

    log.info("Creating breed trait for breed dalmation")
    shorthair = BreedTrait(name="ShortHair", breed=[dalm])

    log.info("Creating breed trait for breeds golden & dalmation")
    friendly = BreedTrait(name="Friendly", breed=[golden, dalm])

    db_session.add_all([longhair, shorthair, friendly])
    db_session.commit()

    assert longhair in golden.breedtrait
    golden.breedtrait.remove(longhair)
    assert longhair not in golden.breedtrait


    log.info("Setting up some nicknames")
    log.info( "spot's id {}".format(spot.id))
    log.info( "goldie's id {}".format(goldie.id))
    log.info( "tom's id {}".format(tom.id))
    log.info( "sue's id {}".format(sue.id))
    sue.pet_associations.append( PetPersonAssociation( pet_id=spot.id, person_id=sue.id, nickname="cheerio"))
    tom.pet_associations.append( PetPersonAssociation( pet_id=spot.id, person_id=tom.id, nickname="buddy"))
    sue.pet_associations.append( PetPersonAssociation( pet_id=goldie.id, person_id=sue.id, nickname="happy"))


    print "The nicknames for spot are: {}".format(spot.nicknames())
    print "The nicknames for goldie are: {}".format(goldie.nicknames())

    
    db_session.close()
    log.info("all done!")