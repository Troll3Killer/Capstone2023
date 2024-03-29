import json

#Opens the JSON file with the output from the dynamic-inventory and loads it into data
with open('gql_inventory.json') as f:
    data = json.load(f)

inventory_output = ''

for device in data['json']['data']['devices']:
    name = device['name']
    ip_address = device['primary_ip4']['address'].split('/')[0]
    inventory_output += name + ' '
    inventory_output += 'ansible_host=' + ip_address + ' '
    inventory_output += 'ansible_network_os=eos\n'

with open('gql_inventory.ini', 'w') as f:
    f.write(inventory_output)


