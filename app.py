from flask import Flask, render_template, request, jsonify, session
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Global store data
store_data = {
    'inventory': [],
    'max_inventory': 8,
    'shoppers': {},
    'transactions': []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shopper/<shopper_id>')
def shopper_page(shopper_id):
    if shopper_id not in store_data['shoppers']:
        return "Shopper not found", 404
    return render_template('shopper.html', 
                         shopper_id=shopper_id, 
                         shopper_name=store_data['shoppers'][shopper_id]['name'])

@app.route('/grocer')
def grocer_page():
    return render_template('grocer.html')

@app.route('/api/register_shopper', methods=['POST'])
def register_shopper():
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    # Check if we already have 2 shoppers
    if len(store_data['shoppers']) >= 2:
        return jsonify({'error': 'Store is full (max 2 shoppers)'}), 400
    
    # Generate shopper ID
    shopper_id = f"S{len(store_data['shoppers']) + 1}"
    
    store_data['shoppers'][shopper_id] = {
        'name': name,
        'cart': []
    }
    
    return jsonify({'shopper_id': shopper_id, 'name': name})

@app.route('/api/inventory')
def get_inventory():
    return jsonify({
        'inventory': store_data['inventory'],
        'count': len(store_data['inventory']),
        'max': store_data['max_inventory']
    })

@app.route('/api/shopper/<shopper_id>/cart')
def get_cart(shopper_id):
    if shopper_id not in store_data['shoppers']:
        return jsonify({'error': 'Shopper not found'}), 404
    
    return jsonify({
        'cart': store_data['shoppers'][shopper_id]['cart'],
        'shopper_name': store_data['shoppers'][shopper_id]['name']
    })

@app.route('/api/grocer/put_item', methods=['POST'])
def put_item():
    data = request.json
    item = data.get('item', '').strip().lower()
    
    if not item:
        return jsonify({'error': 'Item name is required'}), 400
    
    if len(store_data['inventory']) >= store_data['max_inventory']:
        return jsonify({'error': f'Inventory full (max {store_data["max_inventory"]} items)'}), 400
    
    store_data['inventory'].append(item)
    store_data['transactions'].append(f"P {item}")
    
    return jsonify({'success': True, 'inventory': store_data['inventory']})

@app.route('/api/shopper/<shopper_id>/get_item', methods=['POST'])
def get_item(shopper_id):
    if shopper_id not in store_data['shoppers']:
        return jsonify({'error': 'Shopper not found'}), 404
    
    data = request.json
    item = data.get('item', '').strip().lower()
    
    if not item:
        return jsonify({'error': 'Item name is required'}), 400
    
    if item not in store_data['inventory']:
        return jsonify({'error': f'{item} not available'}), 400
    
    # Remove from inventory and add to shopper's cart
    store_data['inventory'].remove(item)
    store_data['shoppers'][shopper_id]['cart'].append(item)
    
    shopper_name = store_data['shoppers'][shopper_id]['name']
    store_data['transactions'].append(f"[{shopper_name}] G {item}")
    
    return jsonify({
        'success': True, 
        'cart': store_data['shoppers'][shopper_id]['cart'],
        'inventory': store_data['inventory']
    })

@app.route('/api/shopper/<shopper_id>/return_item', methods=['POST'])
def return_item(shopper_id):
    if shopper_id not in store_data['shoppers']:
        return jsonify({'error': 'Shopper not found'}), 404
    
    data = request.json
    item = data.get('item', '').strip().lower()
    
    if not item:
        return jsonify({'error': 'Item name is required'}), 400
    
    if item not in store_data['shoppers'][shopper_id]['cart']:
        return jsonify({'error': f'{item} not in your cart'}), 400
    
    if len(store_data['inventory']) >= store_data['max_inventory']:
        return jsonify({'error': 'Cannot return item - inventory is full'}), 400
    
    # Remove from cart and add back to inventory
    store_data['shoppers'][shopper_id]['cart'].remove(item)
    store_data['inventory'].append(item)
    
    shopper_name = store_data['shoppers'][shopper_id]['name']
    store_data['transactions'].append(f"[{shopper_name}] R {item}")
    
    return jsonify({
        'success': True, 
        'cart': store_data['shoppers'][shopper_id]['cart'],
        'inventory': store_data['inventory']
    })

@app.route('/api/transactions')
def get_transactions():
    return jsonify({'transactions': store_data['transactions']})

@app.route('/api/shoppers')
def get_shoppers():
    return jsonify({'shoppers': store_data['shoppers']})

@app.route('/api/grocer/empty_inventory', methods=['POST'])
def empty_inventory():
    if len(store_data['inventory']) == 0:
        return jsonify({'error': 'Inventory is already empty'}), 400
    
    # Clear all items from inventory
    cleared_items = store_data['inventory'].copy()
    store_data['inventory'].clear()
    
    # Add transaction record
    store_data['transactions'].append(f"[GS] Emptied inventory: {', '.join(cleared_items)}")
    
    return jsonify({
        'success': True, 
        'message': f'Cleared {len(cleared_items)} items from inventory',
        'inventory': store_data['inventory']
    })

if __name__ == '__main__':
    app.run(debug=True,port=5656)
