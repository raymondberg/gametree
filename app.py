import os
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

import datetime
from email.utils import parseaddr

from flask import Flask, request
from flask_restful import Resource, Api

import braintree

braintree.Configuration.configure(braintree.Environment.Sandbox,
    os.environ.get('BT_MERCHANT_ID'),
    os.environ.get('BT_PUBLIC_KEY'),
    os.environ.get('BT_PRIVATE_KEY')
)

app = Flask(__name__)
api = Api(app)

players = { }

today = datetime.date.today()
collection = braintree.Customer.search(
    braintree.CustomerSearch.created_at >= today.strftime("%m/%d/%Y")
)

for customer in collection:
  players[customer.email] = customer.id

print("LOADED CUSTOMERS")
print(players)

class Players(Resource):
    def get(self, player_email):
        print(request.form)
        player_handle = players.get(player_email, None)
        if player_handle is None:
                return {}, 404
        else:
            return self.__player_dict(player_email, player_handle)

    def put(self, player_email):
        email = parseaddr(player_email)[1]
        if email == '':
                return {"error": "unable to parse email"}, 422
        if email in players:
                return {"error": "email already registered"}, 403

        players[email] = request.form['player_handle']
        braintree.Customer.create({
                "id": players[email],
                "email": email,
                "credit_card": {
                        "token": players[email],
                        "number": 4111111111111111,
                        "expiration_date": "10/24"
                }
        })
        return self.__player_dict(email, players[email])

    def __player_dict(self, player_email, player_handle):
        return {
           "player_handle": player_handle,
           "player_email": player_email
        }

class Charges(Resource):
    def put(self, player_email):
        amount = request.form['amount']
        if player_email not in players:
                return {"error": "no such user"}, 403
        braintree.Transaction.sale({
                "payment_method_token": players[player_email],
                "amount": amount
        })
        return {"status": "success"}, 200

api.add_resource(Players, '/players/<string:player_email>')
api.add_resource(Charges, '/players/<string:player_email>/charge')

if __name__ == '__main__':
    app.run(debug=True, port=8000)
