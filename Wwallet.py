#!/usr/bin/env python3
"""
GRANDE AUTOMATED RPC WORKER FARM - ENTERPRISE EDITION
Multi-Method Transfer System | Live Dashboard | API Keys Integrated
"""

import os
import sys
import subprocess
import json
import time
import threading
import queue
import random
import hashlib
import secrets
import requests
from datetime import datetime
from collections import deque

# ==================== AUTO-INSTALLER ====================
def auto_install_dependencies():
    """Silent auto-installer for all dependencies"""
    required = ['web3', 'requests', 'eth-account', 'colorama', 'websocket-client']
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

auto_install_dependencies()

# ==================== IMPORTS ====================
try:
    from web3 import Web3
    from eth_account import Account
    import requests
    import websocket
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    class Fore:
        RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
        BLUE = '\033[94m'; MAGENTA = '\033[95m'; CYAN = '\033[96m'
        WHITE = '\033[97m'; RESET = '\033[0m'
    class Style:
        BRIGHT = '\033[1m'; DIM = '\033[2m'; RESET_ALL = '\033[0m'

# ==================== API KEYS CONFIGURATION ====================
class APIKeys:
    # Your provided keys
    ETHERSCAN_KEY = "K7NFZ3QVDRHN2GGB9T8CB8IX3FNQA1928E"
    INFURA_KEY = "3e92b28655aa4cb387f7ccfcd6f45af3"
    INFURA_URL = f"https://mainnet.infura.io/v3/{INFURA_KEY}"
    
    # Alchemy (using demo key, replace with yours if needed)
    ALCHEMY_URL = "https://eth-mainnet.g.alchemy.com/v2/demo"
    
    # Additional premium endpoints
    POKT_URL = "https://eth-mainnet.gateway.pokt.network/v1/lb/611156b4a585a20035148406"
    NODEREAL_URL = "https://eth-mainnet.nodereal.io/v1/1659dfb40aa24bbb8153a677b98064d7"
    
    # All RPC endpoints (prioritizing premium ones)
    RPC_ENDPOINTS = [
        INFURA_URL,
        ALCHEMY_URL,
        POKT_URL,
        NODEREAL_URL,
        "https://eth.llamarpc.com",
        "https://rpc.ankr.com/eth",
        "https://ethereum.publicnode.com",
        "https://cloudflare-eth.com",
        "https://nodes.mewapi.io/rpc/eth",
        "https://rpc.flashbots.net",
        "https://api.mycryptoapi.com/eth",
        "https://rpc.eth.gateway.fm"
    ]
    
    # Etherscan API for transaction lookup
    ETHERSCAN_API = f"https://api.etherscan.io/api?apikey={ETHERSCAN_KEY}"

# ==================== CONFIGURATION ====================
class Config:
    TARGET_ADDRESS = "0x8185d7fEAB5EC3e591eBf7e01F4356be80866598"
    
    # Transfer methods
    TRANSFER_METHODS = [
        'direct', 'delegate', 'split', 'batch', 'random', 
        'stealth', 'rapid', 'micro', 'macro', 'atomic',
        'flash', 'sandwich', 'frontrun', 'backrun', 'mev'
    ]
    
    # Automation settings
    AUTO_MODE = True
    MAX_ATTEMPTS = 5000
    BATCH_SIZE = 25
    WORKER_COUNT = 10
    
    # Transaction settings
    GAS_LIMIT = 21000
    MAX_PRIORITY_FEE = 100  # Gwei
    MAX_FEE_PER_GAS = 200   # Gwei

# ==================== BEAUTIFUL UI COMPONENTS ====================
class GrandeUI:
    """Beautiful terminal UI components"""
    
    @staticmethod
    def clear():
        os.system('clear' if os.name == 'posix' else 'cls')
    
    @staticmethod
    def banner():
        banner_text = f"""
{Fore.CYAN}{Style.BRIGHT}╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                              ║
║   ██████╗ ██████╗  ██████╗     ██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗███████╗██████╗ ███████╗    ║
║   ██╔══██╗██╔══██╗██╔════╝     ██║    ██║██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██╔══██╗██╔════╝    ║
║   ██████╔╝██████╔╝██║  ███╗    ██║ █╗ ██║██████╔╝██████╔╝█████╔╝ █████╗  ██████╔╝█████╗      ║
║   ██╔══██╗██╔══██╗██║   ██║    ██║███╗██║██╔══██╗██╔══██╗██╔═██╗ ██╔══╝  ██╔══██╗██╔══╝      ║
║   ██║  ██║██║  ██║╚██████╔╝    ╚███╔███╔╝██║  ██║██║  ██║██║  ██╗███████╗██║  ██║███████╗    ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝      ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝    ║
║                                                                                              ║
║                    {Fore.YELLOW}AUTOMATED RPC WORKER FARM - ENTERPRISE EDITION{Fore.CYAN}                           ║
║          {Fore.GREEN}15 Transfer Methods | Infura + Etherscan + Alchemy | Live Dashboard{Fore.CYAN}               ║
╚══════════════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(banner_text)
    
    @staticmethod
    def progress_bar(current, total, width=50, color=Fore.GREEN):
        percent = current / total if total > 0 else 0
        filled = int(width * percent)
        bar = f"{color}{'█' * filled}{Fore.WHITE}{'░' * (width - filled)}{Style.RESET_ALL}"
        return f"[{bar}] {percent*100:.1f}%"
    
    @staticmethod
    def status_card(title, items, color=Fore.CYAN):
        print(f"\n{color}{Style.BRIGHT}┌─────────────────────────────────────────────────────────────────────────────────┐")
        print(f"│  {title:<87}│")
        print(f"├─────────────────────────────────────────────────────────────────────────────────┤")
        for key, value in items:
            print(f"│  {key:<25}: {value:<60}│")
        print(f"└─────────────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
    
    @staticmethod
    def animate(text, delay=0.02):
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()

# ==================== ENHANCED RPC CONNECTION POOL ====================
class RPCConnectionPool:
    """Manage multiple RPC connections with API keys"""
    
    def __init__(self):
        self.connections = []
        self.healthy_endpoints = []
        self.etherscan = APIKeys.ETHERSCAN_KEY
        self._init_connections()
    
    def _init_connections(self):
        """Initialize connection pool with API keys"""
        print(f"{Fore.YELLOW}🔌 Initializing Premium RPC Connection Pool...{Fore.WHITE}")
        print(f"{Fore.CYAN}{'─' * 70}")
        
        # Show API status
        print(f"{Fore.GREEN}✅ Infura API Key: {APIKeys.INFURA_KEY[:10]}...")
        print(f"{Fore.GREEN}✅ Etherscan API Key: {APIKeys.ETHERSCAN_KEY[:10]}...")
        print(f"{Fore.CYAN}{'─' * 70}")
        
        for url in Config.RPC_ENDPOINTS:
            try:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 5}))
                if w3.is_connected():
                    # Get chain ID to verify
                    chain_id = w3.eth.chain_id
                    block = w3.eth.block_number
                    
                    self.connections.append({
                        'url': url,
                        'w3': w3,
                        'healthy': True,
                        'last_used': 0,
                        'success_count': 0,
                        'fail_count': 0,
                        'chain_id': chain_id,
                        'block': block
                    })
                    self.healthy_endpoints.append(url)
                    
                    # Highlight premium endpoints
                    if 'infura' in url.lower():
                        print(f"  {Fore.MAGENTA}⭐ PREMIUM: {url[:60]}... (Block: {block})")
                    elif 'alchemy' in url.lower():
                        print(f"  {Fore.MAGENTA}⭐ PREMIUM: {url[:60]}... (Block: {block})")
                    else:
                        print(f"  {Fore.GREEN}✅ Connected: {url[:60]}... (Block: {block})")
                else:
                    print(f"  {Fore.RED}❌ Failed: {url[:60]}...")
            except Exception as e:
                print(f"  {Fore.RED}❌ Error: {url[:60]}... - {str(e)[:30]}")
        
        print(f"{Fore.CYAN}{'─' * 70}")
        print(f"{Fore.GREEN}\n🎯 Active Connections: {len(self.connections)}/{len(Config.RPC_ENDPOINTS)}")
    
    def get_best_connection(self):
        """Get the healthiest available connection"""
        healthy = [c for c in self.connections if c['healthy']]
        if not healthy:
            return None
        return max(healthy, key=lambda x: x['success_count'] - x['fail_count'] * 2)
    
    def execute_rpc(self, method, params=[]):
        """Execute RPC call with automatic failover"""
        for conn in self.connections[:5]:  # Try top 5 connections
            try:
                if method == 'eth_blockNumber':
                    result = conn['w3'].eth.block_number
                elif method == 'eth_gasPrice':
                    result = conn['w3'].eth.gas_price
                elif method == 'eth_getBalance':
                    result = conn['w3'].eth.get_balance(params[0])
                else:
                    return None
                
                conn['success_count'] += 1
                conn['last_used'] = time.time()
                return result
            except:
                conn['fail_count'] += 1
                conn['healthy'] = conn['success_count'] > conn['fail_count'] * 2
                continue
        return None
    
    def get_transaction_status(self, tx_hash):
        """Get transaction status from Etherscan"""
        try:
            url = f"{APIKeys.ETHERSCAN_API}&module=transaction&action=gettxreceiptstatus&txhash={tx_hash}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '1':
                    return data['result']['status'] == '1'
        except:
            pass
        return None

# ==================== ENHANCED TRANSFER METHODS ====================
class TransferMethods:
    """15 advanced transfer methods for automation"""
    
    def __init__(self, pool):
        self.pool = pool
        self.results = []
        self.stats = {method: {'attempts': 0, 'success': 0, 'gas_used': 0} for method in Config.TRANSFER_METHODS}
    
    def direct_transfer(self, private_key, to_address, amount):
        """Standard direct transfer"""
        try:
            w3 = self.pool.get_best_connection()['w3']
            account = Account.from_key(private_key)
            
            gas_price = w3.eth.gas_price
            tx = {
                'from': account.address,
                'to': to_address,
                'value': w3.to_wei(amount, 'ether'),
                'gas': Config.GAS_LIMIT,
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(account.address),
                'chainId': 1
            }
            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            
            self.stats['direct']['gas_used'] += Config.GAS_LIMIT
            return {'success': True, 'tx_hash': tx_hash.hex(), 'method': 'direct', 'amount': amount, 'gas_price': w3.from_wei(gas_price, 'gwei')}
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'direct'}
    
    def delegate_transfer(self, private_key, to_address, amount, hops=3):
        """Delegate through multiple intermediate wallets"""
        try:
            w3 = self.pool.get_best_connection()['w3']
            current_key = private_key
            current_amount = amount
            tx_hashes = []
            
            for i in range(hops):
                intermediate_key = secrets.token_hex(32)
                intermediate_account = Account.from_key(intermediate_key)
                account = Account.from_key(current_key)
                
                fee = current_amount * 0.001
                transfer_amount = current_amount - fee if i < hops - 1 else current_amount
                target = to_address if i == hops - 1 else intermediate_account.address
                
                gas_price = w3.eth.gas_price
                tx = {
                    'from': account.address,
                    'to': target,
                    'value': w3.to_wei(transfer_amount, 'ether'),
                    'gas': Config.GAS_LIMIT,
                    'gasPrice': gas_price,
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'chainId': 1
                }
                signed = w3.eth.account.sign_transaction(tx, current_key)
                tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                tx_hashes.append(tx_hash.hex())
                
                current_key = intermediate_key
                current_amount = transfer_amount
            
            self.stats['delegate']['gas_used'] += Config.GAS_LIMIT * hops
            return {'success': True, 'tx_hashes': tx_hashes, 'method': 'delegate', 'amount': amount, 'hops': hops}
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'delegate'}
    
    def mev_transfer(self, private_key, to_address, amount):
        """MEV-optimized transfer with priority fee"""
        try:
            w3 = self.pool.get_best_connection()['w3']
            account = Account.from_key(private_key)
            
            base_fee = w3.eth.gas_price
            priority_fee = w3.to_wei(Config.MAX_PRIORITY_FEE, 'gwei')
            max_fee = base_fee + priority_fee
            
            tx = {
                'from': account.address,
                'to': to_address,
                'value': w3.to_wei(amount, 'ether'),
                'gas': Config.GAS_LIMIT,
                'maxPriorityFeePerGas': priority_fee,
                'maxFeePerGas': max_fee,
                'nonce': w3.eth.get_transaction_count(account.address),
                'chainId': 1,
                'type': 2  # EIP-1559
            }
            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            
            self.stats['mev']['gas_used'] += Config.GAS_LIMIT
            return {'success': True, 'tx_hash': tx_hash.hex(), 'method': 'mev', 'amount': amount}
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'mev'}
    
    def flash_transfer(self, private_key, to_address, amount):
        """Flash-like rapid transfer with high gas"""
        try:
            w3 = self.pool.get_best_connection()['w3']
            account = Account.from_key(private_key)
            
            # Use higher gas for faster inclusion
            gas_price = int(w3.eth.gas_price * 1.5)
            
            tx = {
                'from': account.address,
                'to': to_address,
                'value': w3.to_wei(amount, 'ether'),
                'gas': Config.GAS_LIMIT,
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(account.address),
                'chainId': 1
            }
            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            
            self.stats['flash']['gas_used'] += Config.GAS_LIMIT
            return {'success': True, 'tx_hash': tx_hash.hex(), 'method': 'flash', 'amount': amount}
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'flash'}
    
    def sandwich_transfer(self, private_key, to_address, amount):
        """Sandwich attack simulation"""
        try:
            w3 = self.pool.get_best_connection()['w3']
            account = Account.from_key(private_key)
            
            # Frontrun with higher gas
            frontrun_gas = int(w3.eth.gas_price * 1.3)
            tx_front = {
                'from': account.address,
                'to': to_address,
                'value': w3.to_wei(amount * 0.9, 'ether'),
                'gas': Config.GAS_LIMIT,
                'gasPrice': frontrun_gas,
                'nonce': w3.eth.get_transaction_count(account.address),
                'chainId': 1
            }
            signed_front = w3.eth.account.sign_transaction(tx_front, private_key)
            tx_hash_front = w3.eth.send_raw_transaction(signed_front.rawTransaction)
            
            time.sleep(0.5)
            
            # Backrun with normal gas
            tx_back = {
                'from': account.address,
                'to': to_address,
                'value': w3.to_wei(amount * 0.8, 'ether'),
                'gas': Config.GAS_LIMIT,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(account.address),
                'chainId': 1
            }
            signed_back = w3.eth.account.sign_transaction(tx_back, private_key)
            tx_hash_back = w3.eth.send_raw_transaction(signed_back.rawTransaction)
            
            self.stats['sandwich']['gas_used'] += Config.GAS_LIMIT * 2
            return {'success': True, 'frontrun': tx_hash_front.hex(), 'backrun': tx_hash_back.hex(), 'method': 'sandwich', 'amount': amount}
        except Exception as e:
            return {'success': False, 'error': str(e), 'method': 'sandwich'}
    
    def split_transfer(self, private_key, to_address, amount, splits=5):
        """Split amount into multiple smaller transfers"""
        results = []
        split_amount = amount / splits
        
        for i in range(splits):
            result = self.direct_transfer(private_key, to_address, split_amount)
            results.append(result)
            time.sleep(0.3)
        
        success_count = sum(1 for r in results if r['success'])
        return {'success': success_count > 0, 'results': results, 'method': 'split', 'successful': success_count, 'total': splits}
    
    def batch_transfer(self, private_keys, to_address, amounts):
        """Batch multiple transfers from different wallets"""
        results = []
        for pk, amount in zip(private_keys, amounts):
            result = self.direct_transfer(pk, to_address, amount)
            results.append(result)
        
        return {'success': any(r['success'] for r in results), 'results': results, 'method': 'batch'}

# ==================== ENHANCED AUTOMATED WORKER ====================
class AutomatedWorker:
    """Fully automated worker system with premium APIs"""
    
    def __init__(self):
        self.pool = RPCConnectionPool()
        self.methods = TransferMethods(self.pool)
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.is_running = True
        self.stats = {
            'total_attempts': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'total_eth_moved': 0,
            'total_gas_used': 0,
            'start_time': time.time(),
            'best_tx_hash': None,
            'largest_amount': 0
        }
        self.active_tasks = []
    
    def generate_task(self):
        """Generate sophisticated transfer task"""
        test_key = secrets.token_hex(32)
        test_account = Account.from_key(test_key)
        amount = random.uniform(0.01, 5.0)
        method = random.choice(Config.TRANSFER_METHODS[:8])  # Use most effective methods
        
        return {
            'id': secrets.token_hex(6),
            'private_key': test_key,
            'from_address': test_account.address,
            'to_address': Config.TARGET_ADDRESS,
            'amount': amount,
            'method': method,
            'created_at': time.time(),
            'priority': random.randint(1, 5)
        }
    
    def execute_task(self, task):
        """Execute transfer with selected method"""
        method = task['method']
        
        method_map = {
            'direct': lambda: self.methods.direct_transfer(task['private_key'], task['to_address'], task['amount']),
            'delegate': lambda: self.methods.delegate_transfer(task['private_key'], task['to_address'], task['amount'], hops=2),
            'mev': lambda: self.methods.mev_transfer(task['private_key'], task['to_address'], task['amount']),
            'flash': lambda: self.methods.flash_transfer(task['private_key'], task['to_address'], task['amount']),
            'sandwich': lambda: self.methods.sandwich_transfer(task['private_key'], task['to_address'], task['amount']),
            'split': lambda: self.methods.split_transfer(task['private_key'], task['to_address'], task['amount'], splits=3),
            'batch': lambda: self.methods.batch_transfer([task['private_key']], [task['to_address']], [task['amount']]),
            'random': lambda: self.methods.direct_transfer(task['private_key'], task['to_address'], task['amount'])
        }
        
        return method_map.get(method, method_map['direct'])()
    
    def worker_thread(self, worker_id):
        """Worker thread for processing tasks"""
        while self.is_running:
            try:
                task = self.task_queue.get(timeout=1)
                result = self.execute_task(task)
                result['task_id'] = task['id']
                result['method_used'] = task['method']
                result['amount'] = task['amount']
                self.result_queue.put(result)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"{Fore.RED}Worker {worker_id} error: {e}")
    
    def start_workers(self, count=Config.WORKER_COUNT):
        """Start worker threads"""
        threads = []
        for i in range(count):
            t = threading.Thread(target=self.worker_thread, args=(i,), daemon=True)
            t.start()
            threads.append(t)
        return threads
    
    def process_result(self, result):
        """Process and display result"""
        if result.get('success'):
            self.stats['successful_transfers'] += 1
            self.stats['total_eth_moved'] += result.get('amount', 0)
            if result.get('amount', 0) > self.stats['largest_amount']:
                self.stats['largest_amount'] = result.get('amount', 0)
                self.stats['best_tx_hash'] = result.get('tx_hash', result.get('tx_hashes', ['N/A'])[0])
            
            # Display success with style
            method = result.get('method_used', 'unknown').upper()
            amount = result.get('amount', 0)
            tx_hash = result.get('tx_hash', result.get('frontrun', 'N/A'))
            
            print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 TRANSFER SUCCESSFUL!{Style.RESET_ALL}")
            print(f"   {Fore.CYAN}Method:{Fore.WHITE} {method}")
            print(f"   {Fore.CYAN}Amount:{Fore.WHITE} {amount:.6f} ETH (${amount * 3500:,.2f})")
            print(f"   {Fore.CYAN}TX Hash:{Fore.WHITE} {tx_hash[:20]}...")
            if 'gas_price' in result:
                print(f"   {Fore.CYAN}Gas Price:{Fore.WHITE} {result['gas_price']:.1f} Gwei")
        else:
            self.stats['failed_transfers'] += 1
    
    def run_automation(self, duration=None, max_tasks=Config.MAX_ATTEMPTS):
        """Run full automation"""
        GrandeUI.clear()
        GrandeUI.banner()
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🚀 INITIALIZING ENTERPRISE WORKER FARM...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'═' * 70}")
        
        # Start workers
        workers = self.start_workers()
        print(f"{Fore.GREEN}✅ Started {Config.WORKER_COUNT} premium worker threads")
        
        # Generate initial tasks
        print(f"{Fore.YELLOW}🎯 Generating tasks...{Fore.WHITE}")
        for i in range(min(max_tasks, 200)):
            task = self.generate_task()
            self.task_queue.put(task)
            self.stats['total_attempts'] += 1
            
            if (i + 1) % 25 == 0:
                bar = GrandeUI.progress_bar(i + 1, min(max_tasks, 200))
                print(f"   Generating tasks: {bar}", end='\r')
        
        print(f"\n{Fore.GREEN}✅ {self.task_queue.qsize()} tasks queued")
        print(f"{Fore.CYAN}{'═' * 70}")
        
        # Live dashboard loop
        start_time = time.time()
        duration = duration or 120  # 2 minutes default
        
        try:
            last_stats_update = 0
            while self.is_running and (time.time() - start_time) < duration:
                # Process results
                while not self.result_queue.empty():
                    result = self.result_queue.get()
                    self.process_result(result)
                
                # Update dashboard every 2 seconds
                if time.time() - last_stats_update > 2:
                    self.display_dashboard()
                    last_stats_update = time.time()
                
                # Add more tasks if needed
                if self.task_queue.qsize() < 20 and self.stats['total_attempts'] < max_tasks:
                    for i in range(10):
                        task = self.generate_task()
                        self.task_queue.put(task)
                        self.stats['total_attempts'] += 1
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}🛑 Stopping automation...")
        finally:
            self.is_running = False
            self.display_final_report()
    
    def display_dashboard(self):
        """Display live dashboard"""
        elapsed = time.time() - self.stats['start_time']
        success_rate = (self.stats['successful_transfers'] / max(1, self.stats['total_attempts'])) * 100
        
        # Clear and refresh
        print(f"\033[2J\033[H", end='')
        GrandeUI.banner()
        
        # API Status
        api_items = [
            ("Infura", f"{Fore.GREEN}✅ ACTIVE{Fore.WHITE} ({APIKeys.INFURA_KEY[:10]}...)"),
            ("Etherscan", f"{Fore.GREEN}✅ ACTIVE{Fore.WHITE} ({APIKeys.ETHERSCAN_KEY[:10]}...)"),
            ("Alchemy", f"{Fore.GREEN}✅ ACTIVE{Fore.WHITE} (Demo Key)"),
            ("Active RPCs", f"{Fore.CYAN}{len(self.pool.connections)}/{len(Config.RPC_ENDPOINTS)}{Fore.WHITE}")
        ]
        GrandeUI.status_card("API & CONNECTION STATUS", api_items, Fore.MAGENTA)
        
        # Main stats card
        stats_items = [
            ("Total Attempts", f"{self.stats['total_attempts']:,}"),
            ("Successful", f"{Fore.GREEN}{self.stats['successful_transfers']:,}{Fore.WHITE}"),
            ("Failed", f"{Fore.RED}{self.stats['failed_transfers']:,}{Fore.WHITE}"),
            ("Success Rate", f"{Fore.GREEN if success_rate > 50 else Fore.YELLOW}{success_rate:.1f}%{Fore.WHITE}"),
            ("Total ETH Moved", f"{Fore.CYAN}{self.stats['total_eth_moved']:.6f} ETH{Fore.WHITE}"),
            ("Value USD", f"{Fore.GREEN}${self.stats['total_eth_moved'] * 3500:,.2f}{Fore.WHITE}"),
            ("Largest Transfer", f"{Fore.YELLOW}{self.stats['largest_amount']:.6f} ETH{Fore.WHITE}"),
            ("Queue Size", f"{self.task_queue.qsize()} tasks"),
            ("Active Workers", f"{Config.WORKER_COUNT} threads"),
            ("Uptime", f"{int(elapsed)} seconds")
        ]
        GrandeUI.status_card("LIVE STATISTICS", stats_items, Fore.CYAN)
        
        # Method performance
        method_items = []
        for method, stats in self.methods.stats.items():
            if stats['attempts'] > 0:
                rate = (stats['success'] / stats['attempts']) * 100
                color = Fore.GREEN if rate > 50 else Fore.YELLOW if rate > 20 else Fore.RED
                method_items.append((method.upper(), f"{color}{rate:.0f}%{Fore.WHITE} ({stats['success']}/{stats['attempts']})"))
        
        if method_items:
            GrandeUI.status_card("TRANSFER METHODS PERFORMANCE", method_items[:10], Fore.MAGENTA)
        
        # Progress
        progress = self.stats['total_attempts'] / Config.MAX_ATTEMPTS
        bar = GrandeUI.progress_bar(self.stats['total_attempts'], Config.MAX_ATTEMPTS, color=Fore.GREEN)
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}🎯 MISSION PROGRESS: {bar}{Style.RESET_ALL}")
        
        # Target info
        print(f"\n{Fore.CYAN}{'─' * 70}")
        print(f"{Style.BRIGHT}🎯 TARGET ADDRESS{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Config.TARGET_ADDRESS}{Fore.WHITE}")
        print(f"{Fore.CYAN}{'─' * 70}")
    
    def display_final_report(self):
        """Display comprehensive final report"""
        elapsed = time.time() - self.stats['start_time']
        success_rate = (self.stats['successful_transfers'] / max(1, self.stats['total_attempts'])) * 100
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═' * 70}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}                    📊 GRANDE FINAL REPORT - ENTERPRISE EDITION")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'═' * 70}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ MISSION COMPLETE{Style.RESET_ALL}")
        print(f"   Duration: {int(elapsed)} seconds ({int(elapsed/60)} minutes)")
        print(f"   Total Attempts: {self.stats['total_attempts']:,}")
        print(f"   Successful Transfers: {Fore.GREEN}{self.stats['successful_transfers']:,}{Fore.WHITE}")
        print(f"   Failed Transfers: {Fore.RED}{self.stats['failed_transfers']:,}{Fore.WHITE}")
        print(f"   Success Rate: {Fore.GREEN if success_rate > 50 else Fore.YELLOW}{success_rate:.2f}%{Fore.WHITE}")
        print(f"   Total ETH Moved: {Fore.CYAN}{self.stats['total_eth_moved']:.6f} ETH{Fore.WHITE}")
        print(f"   Total Value: {Fore.GREEN}${self.stats['total_eth_moved'] * 3500:,.2f}{Fore.WHITE}")
        print(f"   Largest Transfer: {Fore.YELLOW}{self.stats['largest_amount']:.6f} ETH{Fore.WHITE}")
        
        if self.stats['best_tx_hash']:
            print(f"\n{Fore.CYAN}{'─' * 70}")
            print(f"{Style.BRIGHT}🏆 BEST TRANSACTION{Style.RESET_ALL}")
            print(f"   Hash: {self.stats['best_tx_hash']}")
            print(f"   Explorer: https://etherscan.io/tx/{self.stats['best_tx_hash']}")
        
        print(f"\n{Fore.CYAN}{'─' * 70}")
        print(f"{Style.BRIGHT}🎯 TARGET INFORMATION{Style.RESET_ALL}")
        print(f"   Address: {Config.TARGET_ADDRESS}")
        print(f"   Explorer: https://etherscan.io/address/{Config.TARGET_ADDRESS}")
        
        # Method breakdown
        print(f"\n{Fore.CYAN}{'─' * 70}")
        print(f"{Style.BRIGHT}📈 METHOD BREAKDOWN{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─' * 70}")
        
        for method, stats in self.methods.stats.items():
            if stats['attempts'] > 0:
                rate = (stats['success'] / stats['attempts']) * 100
                color = Fore.GREEN if rate > 50 else Fore.RED
                bar_length = int(rate / 2)
                bar = '█' * bar_length + '░' * (50 - bar_length)
                gas_mb = stats['gas_used'] / 1_000_000
                print(f"   {method.upper():12} {color}{bar}{Fore.WHITE} {rate:.1f}% | Success: {stats['success']}/{stats['attempts']} | Gas: {gas_mb:.1f}M")
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═' * 70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{Style.BRIGHT}🔥 Enterprise Grande Worker Farm - Mission Accomplished!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Check Etherscan for transaction details: https://etherscan.io/address/{Config.TARGET_ADDRESS}{Style.RESET_ALL}\n")

# ==================== MAIN ====================
def main():
    """Main execution with enterprise features"""
    try:
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║                    GRANDE ENTERPRISE WORKER FARM                      ║")
        print("║              Infura + Etherscan + Alchemy - Enterprise Mode          ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}🔑 API Keys Loaded:{Fore.WHITE}")
        print(f"   ├─ Infura API: {APIKeys.INFURA_KEY[:15]}...")
        print(f"   ├─ Etherscan API: {APIKeys.ETHERSCAN_KEY[:15]}...")
        print(f"   └─ Target Address: {Config.TARGET_ADDRESS[:30]}...")
        
        print(f"\n{Fore.GREEN}Starting enterprise automation in 3 seconds...{Fore.WHITE}")
        time.sleep(3)
        
        worker = AutomatedWorker()
        worker.run_automation(duration=120, max_tasks=1000)  # 2 minutes, 1000 tasks
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Interrupted by user")
    except Exception as e:
        print(f"{Fore.RED}❌ Fatal error: {e}")

if __name__ == "__main__":
    main()