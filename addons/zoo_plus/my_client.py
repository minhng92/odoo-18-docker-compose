from xml_rpc import XMLRPC_API, myprint

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# please change the credential!
ODOO_BACKEND = 'https://odoo.minhng.info' # http://localhost:10014
ODOO_DB = 'CO200912-1'
ODOO_USER = 'admin'
ODOO_PASS = 'admin'

def main():
    client = XMLRPC_API(url=ODOO_BACKEND, db=ODOO_DB, username=ODOO_USER, password=ODOO_PASS)
    print(client.call(model_name="zoo.animal", method="get_basic_animal_info", params=[False, 3]))
    # {'name': 'Polar Bear', 'gender': 'female', 'age': 5, 'feed_visitor_message': ''}

if __name__ == "__main__":
    main()