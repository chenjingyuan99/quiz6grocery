import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, render_template, request, jsonify
from shared.database import store

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'stocker-secret-key')

@app.route('/')
def index():
    return render_template('stocker.html')

@app.route('/api/inventory')
def get_inventory():
    inventory = store.get_inventory()
    return jsonify({
        'inventory': inventory,
        'count': len(inventory),
        'max': store.max_inventory
    })

@app.route('/api/put_item', methods=['POST'])
def put_item():
    data = request.json
    items_input = data.get('item', '').strip()
    
    if not items_input:
        return jsonify({'error': 'Item name(s) required'}), 400
    
    items = [item.strip() for item in items_input.split(',') if item.strip()]
    if not items:
        return jsonify({'error': 'No valid items provided'}), 400
    
    success, message = store.add_items_to_inventory(items)
    
    if success:
        return jsonify({'success': True, 'message': message, 'inventory': store.get_inventory()})
    else:
        return jsonify({'error': message}), 400

@app.route('/api/empty_inventory', methods=['POST'])
def empty_inventory():
    success, message = store.empty_inventory()
    
    if success:
        return jsonify({'success': True, 'message': message, 'inventory': store.get_inventory()})
    else:
        return jsonify({'error': message}), 400

@app.route('/api/shoppers')
def get_shoppers():
    return jsonify({'shoppers': store.get_shoppers()})

@app.route('/api/transactions')
def get_transactions():
    return jsonify({'transactions': store.get_transactions()})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
