from data.db_session import DataBase
from flask import Flask, jsonify, request, abort
import datetime

app = Flask(__name__)


def convert_data(userdict) -> dict:
    dct = {str(key): value for key, value in userdict.items()}
    dct.pop("password", None)
    if "photo" in dct:
        dct["photo"] = tuple(dct["photo"])  # json.loads(dct["photo"])
    if "dob" in dct:
        dct["age"] = int((datetime.date.today() - dct.pop("dob")) / 365.25)
    return dct


def add_result(dct: dict = None, val: bool = True) -> dict:
    if dct is None:
        dct = {}
    dct["result"] = val
    return dct


@app.route('/', methods=['GET'])
def index():
    print("HELLO")
    return jsonify("Hello, World!")


@app.route('/user/<int:userid>', methods=['GET'])
def get_user(userid):
    db = DataBase()
    user = db.get_user(userid)
    return jsonify(convert_data(user._asdict()))


@app.route('/login', methods=['POST', 'GET'])
def sign_user():
    print(request.json)
    if "email" not in request.json and "password" not in request.json:
        abort(400)
    db = DataBase()
    user = db.login(request.json["email"])
    if user and db.check_password(user["id"], request.json["password"]):
        return jsonify(add_result(convert_data(user._asdict())))
    return jsonify(add_result(val=False))


@app.route('/register', methods=['POST'])  # "%Y-%m-%d" format date
def register():
    if not request.json and any((key not in request.json
                                 for key in ("firstname", "lastname", "sex", "date", "email",
                                             "password"))):  # add check params
        abort(400)
    db = DataBase()
    return add_result(val=db.add_user(**request.json))


@app.route('/create_event')
def create_event():  # "%Y-%m-%d %H:%M:%S" format date
    if any(key not in request.json for key in
           ("title", "geoX", "geoY", "start", "organizerid", "maxCountMembers")):
        abort(400)
    db = DataBase()
    return add_result(val=db.add_events(**request.json))

@app.route('/visit_event')
def visit_events():
    if any(key not in request.json for key in ("userid", "eventid")):
        abort(400)
    db = DataBase()
    return add_result(val=db.visit_event(**request.json))


if __name__ == '__main__':
    app.run()
    pass
