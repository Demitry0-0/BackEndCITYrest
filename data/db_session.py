import datetime
from sqlalchemy import MetaData, create_engine, \
    Table, String, Column, Integer, BLOB, TEXT, REAL, DATE, DATETIME, \
    insert, update, select, and_, \
    ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
import json

__factory = None


class DataBase:
    __connection = None
    __users = Table()
    __events = Table()
    __defaultphoto = "static\\img\\test.bmp"

    def convert_photo(self, filename):
        with open(filename, mode="rb") as file:
            return file.read()

    def convert_password(self, password):
        return generate_password_hash(password)

    def check_password(self, userid, password) -> bool:
        sel = select([self.__users]).where(
            self.__users.c.id == userid
        ).limit(1)
        return check_password_hash(self.__connection.execute(sel).first()["password"], password)

    def __init__(self, db_file="db/base.sqlite", drop=False):
        if not db_file or not db_file.strip():
            raise Exception("Необходимо указать файл базы данных.")

        conn_str = f'sqlite:///{db_file.strip()}?check_e_thread=False'
        print(f"Подключение к базе данных по адресу {conn_str}")

        metadata = MetaData()

        engine = create_engine(conn_str, echo=False)
        # users.txt

        self.__users = Table("users", metadata,
                             Column("id", Integer(), primary_key=True, unique=True, index=True),
                             Column('firstname', String(64), nullable=False),
                             Column('lastname', String(64), nullable=False),
                             Column('sex', String(1), nullable=False),
                             Column('email', String(64), nullable=False, unique=True),
                             # Column('phone', String(12), nullable=False, unique=True),
                             Column('password', String(102), nullable=False),
                             Column('dob', DATE(), nullable=False),
                             Column('specification', TEXT(), nullable=False, default=""),
                             Column('rating', Integer(), nullable=False, default=0),
                             Column('visited', TEXT, nullable=False, default=json.dumps([])),
                             Column('subscriber', Integer(), nullable=False, default=0),
                             Column('photo', BLOB(), nullable=False,
                                    default=self.convert_photo(self.__defaultphoto))
                             )

        self.__events = Table("events", metadata,
                              Column('id', Integer, primary_key=True, unique=True, index=True),
                              Column('title', String(128), nullable=False),
                              Column('geoX', REAL, nullable=False),
                              Column('geoY', REAL, nullable=False),
                              Column('start', DATETIME, nullable=False),
                              Column('organizerid', Integer, ForeignKey(self.__users.c.id),
                                     nullable=False),
                              Column('countMembers', Integer, nullable=False, default=0),
                              Column('maxCountMembers', Integer, nullable=False, default=0),
                              # 0 - inf
                              Column('members', TEXT, nullable=False, default=json.dumps([])),
                              Column('ageFrom', Integer, nullable=False, default=0),
                              Column('ageTo', Integer, nullable=False, default=127),
                              Column('price', Integer, nullable=False, default=0),
                              Column('duration', Integer, nullable=False),
                              Column('genre', TEXT, nullable=False, default=''),
                              Column('photo', BLOB(), nullable=False,
                                     default=self.convert_photo(self.__defaultphoto))
                              )

        if drop:
            metadata.drop_all(engine)
            quit()
        metadata.create_all(engine)

        self.__connection = engine.connect()

    def check_email(self, email):
        sel = select(self.__users).where(self.__users.c.email == email).limit(1)
        s = self.__connection.execute(sel).first()
        return bool(s)

    def add_user(self, firstname, lastname, sex, date: str, email, password):
        try:
            ins = insert(self.__users).values(
                firstname=firstname,
                lastname=lastname,
                sex=sex,
                dob=datetime.datetime.strptime(date, "%Y-%m-%d"),
                email=email,
                password=self.convert_password(password)
            )
            if self.check_email(email):
                return False
            self.__connection.execute(ins)
            return True
        except ValueError:
            return False

    def get_user(self, userid):
        sel = select([self.__users]).where(
            self.__users.c.id == userid
        ).limit(1)
        s = self.__connection.execute(sel).first()
        # s._asdict() => dict
        return s

    def login(self, email):
        sel = select([self.__users]).where(
            self.__users.c.email == email
        ).limit(1)
        s = self.__connection.execute(sel).first()
        return s

    def subscribe(self, userid):
        upd = update(self.__users).where(
            self.__users.c.id == userid
        ).values(
            subscriber=self.__users.c.subscriber + 1
        )
        self.__connection.execute(upd)

    def unsubscribe(self, userid):
        upd = update(self.__users).where(
            and_(self.__users.c.id == userid,
                 self.__users.c.subscriber > 0)
        ).values(
            subscriber=self.__users.c.subscriber - 1
        )
        self.__connection.execute(upd)

    def set_photo(self, userid, photo):
        upd = update(self.__users).where(
            self.__users.c.id == userid
        ).values(
            photo=photo
        )
        self.__connection.execute(upd)

    def add_visited_events(self, userid, eventid):
        sel = select([self.__users]).where(
            self.__users.c.id == userid
        ).limit(1)
        s = self.__connection.execute(sel).first()

        events = json.loads(s["visited"])
        if eventid not in events:
            events.append(eventid)

        upd = update(self.__users).where(
            self.__users.c.id == userid
        ).values(
            visited=json.dumps(events)
        )
        self.__connection.execute(upd)


    # "%Y-%m-%d %H:%M:%S" format date
    def add_events(self, organizedid, title, geoX, geoY, start, countMembers,
                   maxCountMembers, duration, ageFrom=0, ageTo=127, price=0, genre=''):

        try:
            ins = insert(self.__users).values(
                organizedid=organizedid,
                title=title,
                geoX=geoX,
                geoY=geoY,
                start=datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S"),
                countMembers=countMembers,
                maxCountMembers=maxCountMembers,
                duration=duration,
                ageFrom=ageFrom,
                ageTo=ageTo,
                price=price,
                genre=genre
            )
            self.__connection.execute(ins)
            return True
        except ValueError:
            return False

    def get_event(self, eventid):
        sel = select([self.__events]).where(
            self.__events.c.id == eventid
        ).limit(1)
        s = self.__connection.execute(sel).first()
        return s

    def visit_event(self, userid, eventid):
        s = self.get_event(eventid)
        if s["countMembers"] >= s["maxCountMembers"]:
            return False

        ls = json.loads(s["members"])

        if userid not in ls:
            ls.append(userid)

        upd = update(self.__events).where(
            self.__events.c.id == eventid
        ).values(
            members=json.dumps(ls),
            countMembers=self.__events.c.countMembers + 1
        )
        self.__connection.execute(upd)
        return True

