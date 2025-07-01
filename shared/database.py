import redis
import json
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Redis connection for shared data store
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6380)),
    password=os.getenv('REDIS_PASSWORD', None),
    decode_responses=True,
    ssl=True,
    username=None
)

class GroceryStore:
    def __init__(self):
        self.max_inventory = 8
        
    def get_inventory(self):
        inventory = redis_client.get('inventory')
        return json.loads(inventory) if inventory else []
    
    def set_inventory(self, inventory):
        redis_client.set('inventory', json.dumps(inventory))
    
    def get_shoppers(self):
        shoppers = redis_client.get('shoppers')
        return json.loads(shoppers) if shoppers else {}
    
    def set_shoppers(self, shoppers):
        redis_client.set('shoppers', json.dumps(shoppers))
    
    def get_transactions(self):
        transactions = redis_client.get('transactions')
        return json.loads(transactions) if transactions else []
    
    def add_transaction(self, transaction):
        transactions = self.get_transactions()
        transactions.append(transaction)
        redis_client.set('transactions', json.dumps(transactions))
    
    def add_items_to_inventory(self, items):
        inventory = self.get_inventory()
        if len(inventory) + len(items) > self.max_inventory:
            return False, f"Cannot add {len(items)} items. Would exceed inventory limit of {self.max_inventory}"
        
        for item in items:
            inventory.append(item.lower().strip())
            self.add_transaction(f"P {item.lower().strip()}")
        
        self.set_inventory(inventory)
        return True, f"Added {len(items)} items: {', '.join(items)}"
    
    def empty_inventory(self):
        inventory = self.get_inventory()
        if not inventory:
            return False, "Inventory is already empty"
        
        self.set_inventory([])
        self.add_transaction(f"[GS] Emptied inventory: {', '.join(inventory)}")
        return True, f"Cleared {len(inventory)} items from inventory"
    
    def register_shopper(self, name):
        shoppers = self.get_shoppers()
        if len(shoppers) >= 2:
            return False, "Store is full (max 2 shoppers)", None
        
        shopper_id = f"S{len(shoppers) + 1}"
        shoppers[shopper_id] = {'name': name, 'cart': []}
        self.set_shoppers(shoppers)
        return True, f"Welcome {name}!", shopper_id
    
    def get_items(self, shopper_id, items):
        inventory = self.get_inventory()
        shoppers = self.get_shoppers()
        
        if shopper_id not in shoppers:
            return False, "Shopper not found"
        
        unavailable_items = []
        obtained_items = []
        
        for item in items:
            item = item.lower().strip()
            if item in inventory:
                inventory.remove(item)
                shoppers[shopper_id]['cart'].append(item)
                obtained_items.append(item)
                self.add_transaction(f"[{shoppers[shopper_id]['name']}] G {item}")
            else:
                unavailable_items.append(item)
        
        self.set_inventory(inventory)
        self.set_shoppers(shoppers)
        
        messages = []
        if obtained_items:
            messages.append(f"Got: {', '.join(obtained_items)}")
        if unavailable_items:
            messages.append(f"Not available: {', '.join(unavailable_items)}")
        
        return len(obtained_items) > 0, '; '.join(messages)
    
    def return_items(self, shopper_id, items):
        inventory = self.get_inventory()
        shoppers = self.get_shoppers()
        
        if shopper_id not in shoppers:
            return False, "Shopper not found"
        
        not_in_cart = []
        returned_items = []
        cannot_return = []
        
        for item in items:
            item = item.lower().strip()
            if item not in shoppers[shopper_id]['cart']:
                not_in_cart.append(item)
            elif len(inventory) >= self.max_inventory:
                cannot_return.append(item)
            else:
                shoppers[shopper_id]['cart'].remove(item)
                inventory.append(item)
                returned_items.append(item)
                self.add_transaction(f"[{shoppers[shopper_id]['name']}] R {item}")
        
        self.set_inventory(inventory)
        self.set_shoppers(shoppers)
        
        messages = []
        if returned_items:
            messages.append(f"Returned: {', '.join(returned_items)}")
        if not_in_cart:
            messages.append(f"Not in cart: {', '.join(not_in_cart)}")
        if cannot_return:
            messages.append(f"Cannot return (inventory full): {', '.join(cannot_return)}")
        
        return len(returned_items) > 0, '; '.join(messages)

store = GroceryStore()
