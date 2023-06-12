from flask import Flask ,request , jsonify
from elasticsearch import Elasticsearch
from werkzeug.middleware.profiler import ProfilerMiddleware
import pickle
import pandas as pd
import json
import os
from dotenv import load_dotenv
app=Flask(__name__)
load_dotenv()
class ExcludePostProfilerMiddleware:
    def __init__(self, app, profile_dir):
        self.app = app
        self.profiler_middleware = ProfilerMiddleware(self.app, profile_dir=profile_dir)

    def __call__(self, environ, start_response):
        if environ["REQUEST_METHOD"] == "POST":
            return self.app(environ, start_response)
        return self.profiler_middleware(environ, start_response)
app.wsgi_app = ExcludePostProfilerMiddleware(app.wsgi_app, profile_dir='./profile')



# Create the client instance

#es = Elasticsearch(hosts=["http://localhost:9200"])
#Y3I3SXBZZ0JWRTNEcHpWZU5GOFc6ck5nUnh6ZkVTMG1COU11aUpkZF9tdw==
es = Elasticsearch(
    cloud_id=os.getenv("CLOUD_ID"),
    api_key=os.getenv("API_KEY"),
)
## THIS IS THE OCE TO CREATE INDEX IN THE ELASTC SEARCH AND LOAD THE DATA IN IT

index_name = 'products_index'  # Choose a suitable index name

# mapping = {
#     'properties': {
#         'product_id': {'type': 'text'},
#         'product_name': {'type': 'text'}
#     }
# }

# es.indices.create(index=index_name, ignore=400)
# es.indices.put_mapping(index=index_name, body=mapping)

# def index_product(product_id, product_name):
#     document = {
#         'product_id': product_id,
#         'product_name': product_name
#     }
#     es.index(index=index_name, body=document, id=product_id)


@app.route('/search', methods=['POST'])
def search():
    req=request.get_json()
    data=req["keyword"].lower()
    body = {
    'query': {
        'wildcard': {
            'product_name': {
                'value': '*' + data + '*',
                'boost': 1.0,
                'case_insensitive': True
                }
            }
        }
    }
    response = es.search(index=index_name, body=body)
    hits = response['hits']['hits']
    print(hits)
    products=[]
    ids=[]
    for hit in hits:

      products.append(hit['_source']['product_name'])
      ids.append(hit['_source']['product_id'])
    d = pd.DataFrame({'products': products, 'product_id': ids})
    data = d.to_dict(orient='records')

    # Convert the data to JSON
    json_data = json.dumps(data)
    return json_data


# product_dict = pickle.load(open('product_dict.pkl','rb'))
# df=pd.DataFrame(product_dict)
# df.reset_index(inplace=True)
# for i in range(len(df)):
#   index_product(df["product_id"][i],df["products"][i])


@app.route('/webhook', methods=['POST'])
def webhook():
    request_data = request.get_json()
    intent = request_data['queryResult']['intent']['displayName']

    if intent == 'order_tracking':
        order_id = request_data['queryResult']['parameters']['awb_number']
        order_id= "{:.0f}".format(order_id)


        # Query the database to retrieve the order status based on the orderId
        order_status = query_order_status_from_database(order_id)

        # Format the response
        #order_status=list(order_status)
        # Send the response back to Dialogflow
        response = {
    "fulfillmentText": "This is a text response",
    "fulfillmentMessages": [
      {
        "text": {
          "text": [
            "your order status is {}".format(order_status)
          ]
        }
      }
    ],
    "source": "example.com",
    "payload": {
      "google": {
        "expectUserResponse": "true",
        "richResponse": {
          "items": [
            {
              "simpleResponse": {
                "textToSpeech": "this is a simple response"
              }
            }
          ]
        }
      },
      "facebook": {
        "text": "Hello, Facebook!"
      },
      "slack": {
        "text": "This is a text response for Slack."
      }
    }
  }
        return jsonify(response)

    return jsonify({})  # Return an empty response for other intents

# Function to query the order status from the database
def query_order_status_from_database(order_id):
    # Code to connect to your database and retrieve the order status based on the orderId
    # Replace this with your actual implementation
    # Example:
    orders = {
        '123': 'In progress',
        '456': 'Delivered',
        '789': 'Cancelled'
    }

    return orders[order_id]

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int("3000"),debug=True)

