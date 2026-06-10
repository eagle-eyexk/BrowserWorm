#!/usr/bin/env python3
"""
RPC WORKER FARM - Delegate Chain Transfer System
Multi-Threaded Workers | Ethical Transfer Algorithms | Blockchain Automation
Target: 0x8185d7fEAB5EC3e591eBf7e01F4356be80866598
"""

import json
import time
import threading
import queue
import requests
import hashlib
import secrets
from web3 import Web3
from eth_account import Account
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== CONFIGURATION ====================
class Config:
    # Target address for all transfers
    TARGET_ADDRESS = "0x8185d7fEAB5EC3e591eBf7e01F4356be80866598"
    
    # RPC Endpoints for worker distribution
    RPC_ENDPOINTS = [
        "https://eth.llamarpc.com",
        "https://rpc.ankr.com/eth",
        "https://ethereum.publicnode.com",
        "https://nodes.mewapi.io/rpc/eth",
        "https://eth-mainnet.public.blastapi.io",
        "https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
        "https://cloudflare-eth.com",
        "https://eth-mainnet.g.alchemy.com/v2/demo"
    ]
    
    # Worker configuration
    MAX_WORKERS = 10
    WORKER_BATCH_SIZE = 50
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 2
    
    # Gas optimization
    MAX_GAS_PRICE_GWEI = 100
    MIN_GAS_PRICE_GWEI = 10
    GAS_LIMIT = 21000
    
    # Delegate chain settings
    MAX_DELEGATION_DEPTH = 5
    DELEGATE_FEE_PERCENT = 0.1  # 0.1% fee for delegate chain
    
    # Ethics settings
    ETHICS_MODE = True
    MAX_TRANSFER_AMOUNT_ETH = 1000
    DAILY_LIMIT_ETH = 10000
    COOLDOWN_SECONDS = 60

# ==================== DATA MODELS ====================
@dataclass
class WorkerTask:
    """Worker task data structure"""
    task_id: str
    from_address: str
    to_address: str
    amount_wei: int
    private_key: str
    delegate_chain: List[str]
    priority: int = 1
    retry_count: int = 0
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    tx_hash: Optional[str] = None

@dataclass
class DelegateNode:
    """Delegate chain node"""
    address: str
    private_key: str
    balance_wei: int
    level: int
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    transactions: List[str] = field(default_factory=list)

@dataclass
class TransferRecord:
    """Record of completed transfer"""
    tx_hash: str
    from_address: str
    to_address: str
    amount_eth: float
    gas_used: int
    gas_price_gwei: float
    timestamp: float
    delegate_chain: List[str]
    status: str

# ==================== RPC WORKER ====================
class RPCWorker:
    """Individual RPC worker for blockchain operations"""
    
    def __init__(self, worker_id: int, rpc_url: str):
        self.worker_id = worker_id
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.connected = self.w3.is_connected()
        self.stats = {
            'tasks_processed': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'total_gas_used': 0,
            'start_time': time.time()
        }
        self.is_running = True
        
    def check_connection(self) -> bool:
        """Verify RPC connection"""
        if not self.connected:
            self.connected = self.w3.is_connected()
        return self.connected
    
    def get_gas_price(self) -> int:
        """Get optimized gas price"""
        try:
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price, 'gwei')
            
            # Clamp to configured limits
            if gas_price_gwei > Config.MAX_GAS_PRICE_GWEI:
                gas_price = self.w3.to_wei(Config.MAX_GAS_PRICE_GWEI, 'gwei')
            elif gas_price_gwei < Config.MIN_GAS_PRICE_GWEI:
                gas_price = self.w3.to_wei(Config.MIN_GAS_PRICE_GWEI, 'gwei')
                
            return gas_price
        except:
            return self.w3.to_wei(Config.MIN_GAS_PRICE_GWEI, 'gwei')
    
    def get_balance(self, address: str) -> int:
        """Get address balance in Wei"""
        try:
            return self.w3.eth.get_balance(address)
        except:
            return 0
    
    def execute_transfer(self, task: WorkerTask) -> Optional[Dict]:
        """Execute transfer with retry logic"""
        if not self.check_connection():
            print(f"⚠️ Worker {self.worker_id}: RPC not connected")
            return None
        
        try:
            # Get current gas price
            gas_price = self.get_gas_price()
            
            # Build transaction
            tx = {
                'from': task.from_address,
                'to': task.to_address,
                'value': task.amount_wei,
                'gas': Config.GAS_LIMIT,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(task.from_address),
                'chainId': 1
            }
            
            # Sign transaction
            signed = self.w3.eth.account.sign_transaction(tx, task.private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt['status'] == 1:
                # Update stats
                self.stats['successful_transfers'] += 1
                self.stats['total_gas_used'] += receipt['gasUsed']
                
                return {
                    'tx_hash': tx_hash_hex,
                    'gas_used': receipt['gasUsed'],
                    'gas_price_gwei': self.w3.from_wei(gas_price, 'gwei'),
                    'status': 'success'
                }
            else:
                self.stats['failed_transfers'] += 1
                return {'status': 'failed', 'reason': 'Transaction reverted'}
                
        except Exception as e:
            self.stats['failed_transfers'] += 1
            print(f"❌ Worker {self.worker_id} error: {e}")
            return None
        
        finally:
            self.stats['tasks_processed'] += 1
    
    def get_stats(self) -> Dict:
        """Get worker statistics"""
        elapsed = time.time() - self.stats['start_time']
        return {
            'worker_id': self.worker_id,
            'connected': self.connected,
            'tasks_processed': self.stats['tasks_processed'],
            'successful': self.stats['successful_transfers'],
            'failed': self.stats['failed_transfers'],
            'success_rate': (self.stats['successful_transfers'] / max(1, self.stats['tasks_processed'])) * 100,
            'total_gas_used': self.stats['total_gas_used'],
            'uptime': elapsed,
            'tps': self.stats['tasks_processed'] / max(1, elapsed)
        }

# ==================== DELEGATE CHAIN MANAGER ====================
class DelegateChainManager:
    """Manage delegate chains for ethical transfers"""
    
    def __init__(self):
        self.delegate_nodes: Dict[str, DelegateNode] = {}
        self.active_chains: List[List[str]] = []
        self.chain_counter = 0
        
    def create_delegate_chain(self, root_private_key: str, root_address: str, depth: int = 3) -> List[DelegateNode]:
        """Create a delegate chain of wallets"""
        chain = []
        current_private = root_private_key
        current_address = root_address
        current_level = 0
        
        for i in range(min(depth, Config.MAX_DELEGATION_DEPTH)):
            # Generate intermediate wallet
            intermediate_private = secrets.token_hex(32)
            intermediate_account = Account.from_key(intermediate_private)
            intermediate_address = intermediate_account.address
            
            # Create delegate node
            node = DelegateNode(
                address=intermediate_address,
                private_key=intermediate_private,
                balance_wei=0,
                level=current_level,
                parent=current_address if current_level > 0 else None
            )
            
            self.delegate_nodes[intermediate_address] = node
            chain.append(node)
            
            current_address = intermediate_address
            current_private = intermediate_private
            current_level += 1
        
        # Add target as final node
        target_node = DelegateNode(
            address=Config.TARGET_ADDRESS,
            private_key="",  # Target address doesn't need private key
            balance_wei=0,
            level=current_level,
            parent=current_address
        )
        self.delegate_nodes[Config.TARGET_ADDRESS] = target_node
        chain.append(target_node)
        
        # Store chain
        chain_addresses = [node.address for node in chain]
        self.active_chains.append(chain_addresses)
        self.chain_counter += 1
        
        print(f"🔗 Created delegate chain #{self.chain_counter} with {len(chain)} hops")
        for i, node in enumerate(chain):
            print(f"   Level {i}: {node.address[:10]}...")
        
        return chain
    
    def calculate_chain_transfer(self, chain: List[DelegateNode], amount_wei: int) -> List[WorkerTask]:
        """Calculate transfers through delegate chain"""
        tasks = []
        current_amount = amount_wei
        
        for i in range(len(chain) - 1):
            from_node = chain[i]
            to_node = chain[i + 1]
            
            # Calculate fee (except for last hop)
            if i < len(chain) - 2:
                fee = int(current_amount * (Config.DELEGATE_FEE_PERCENT / 100))
                transfer_amount = current_amount - fee
            else:
                transfer_amount = current_amount
                fee = 0
            
            # Create task
            task = WorkerTask(
                task_id=f"delegate_{self.chain_counter}_{i}_{int(time.time())}",
                from_address=from_node.address,
                to_address=to_node.address,
                amount_wei=transfer_amount,
                private_key=from_node.private_key,
                delegate_chain=[node.address for node in chain],
                priority=1
            )
            tasks.append(task)
            
            current_amount = transfer_amount
        
        return tasks
    
    def get_chain_balance(self, chain: List[DelegateNode]) -> int:
        """Get total balance of delegate chain"""
        total = 0
        for node in chain:
            if node.private_key:
                try:
                    w3 = Web3(Web3.HTTPProvider(Config.RPC_ENDPOINTS[0]))
                    balance = w3.eth.get_balance(node.address)
                    total += balance
                except:
                    pass
        return total

# ==================== ETHICS ALGORITHM ====================
class EthicsAlgorithm:
    """Ethical transfer algorithms and limits"""
    
    def __init__(self):
        self.daily_transfers: Dict[str, float] = {}
        self.cooldown_timers: Dict[str, float] = {}
        self.approved_wallets: set = set()
        
    def validate_transfer(self, from_address: str, amount_eth: float) -> tuple[bool, str]:
        """Validate transfer against ethics rules"""
        
        # Check cooldown
        if from_address in self.cooldown_timers:
            elapsed = time.time() - self.cooldown_timers[from_address]
            if elapsed < Config.COOLDOWN_SECONDS:
                return False, f"Cooldown active: {Config.COOLDOWN_SECONDS - elapsed:.0f}s remaining"
        
        # Check daily limit
        daily_total = self.daily_transfers.get(from_address, 0)
        if daily_total + amount_eth > Config.DAILY_LIMIT_ETH:
            return False, f"Daily limit exceeded: {Config.DAILY_LIMIT_ETH} ETH"
        
        # Check max transfer
        if amount_eth > Config.MAX_TRANSFER_AMOUNT_ETH:
            return False, f"Transfer exceeds max: {Config.MAX_TRANSFER_AMOUNT_ETH} ETH"
        
        return True, "Valid"
    
    def record_transfer(self, from_address: str, amount_eth: float):
        """Record transfer for tracking"""
        self.daily_transfers[from_address] = self.daily_transfers.get(from_address, 0) + amount_eth
        self.cooldown_timers[from_address] = time.time()
    
    def add_approved_wallet(self, address: str):
        """Add approved wallet to whitelist"""
        self.approved_wallets.add(address.lower())
    
    def is_approved(self, address: str) -> bool:
        """Check if wallet is approved"""
        return address.lower() in self.approved_wallets

# ==================== WORKER MANAGER ====================
class WorkerManager:
    """Manage RPC workers and task distribution"""
    
    def __init__(self):
        self.workers: List[RPCWorker] = []
        self.task_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.is_running = True
        self.ethics = EthicsAlgorithm()
        self.delegate_manager = DelegateChainManager()
        self.transfer_records: List[TransferRecord] = []
        
    def initialize_workers(self):
        """Initialize RPC workers"""
        print(f"🚀 Initializing {Config.MAX_WORKERS} RPC workers...")
        
        for i in range(min(Config.MAX_WORKERS, len(Config.RPC_ENDPOINTS))):
            worker = RPCWorker(i, Config.RPC_ENDPOINTS[i])
            if worker.check_connection():
                self.workers.append(worker)
                print(f"✅ Worker {i} connected to {Config.RPC_ENDPOINTS[i][:30]}...")
            else:
                print(f"❌ Worker {i} failed to connect")
        
        print(f"🎯 Active workers: {len(self.workers)}")
    
    def create_delegate_transfer(self, source_private_key: str, amount_eth: float, chain_depth: int = 3) -> Optional[List[WorkerTask]]:
        """Create delegate chain transfer to target"""
        
        # Validate ethics
        source_account = Account.from_key(source_private_key)
        is_valid, message = self.ethics.validate_transfer(source_account.address, amount_eth)
        
        if not is_valid and Config.ETHICS_MODE:
            print(f"❌ Ethics validation failed: {message}")
            return None
        
        # Create delegate chain
        chain = self.delegate_manager.create_delegate_chain(
            source_private_key, 
            source_account.address, 
            chain_depth
        )
        
        # Calculate transfer tasks
        amount_wei = Web3.to_wei(amount_eth, 'ether')
        tasks = self.delegate_manager.calculate_chain_transfer(chain, amount_wei)
        
        # Add to queue
        for task in tasks:
            self.task_queue.put(task)
        
        print(f"📋 Created {len(tasks)} delegate tasks for {amount_eth} ETH")
        return tasks
    
    def direct_transfer(self, from_private_key: str, to_address: str, amount_eth: float) -> Optional[WorkerTask]:
        """Direct transfer to target"""
        
        # Validate
        from_account = Account.from_key(from_private_key)
        is_valid, message = self.ethics.validate_transfer(from_account.address, amount_eth)
        
        if not is_valid and Config.ETHICS_MODE:
            print(f"❌ Ethics validation failed: {message}")
            return None
        
        # Create task
        amount_wei = Web3.to_wei(amount_eth, 'ether')
        task = WorkerTask(
            task_id=f"direct_{int(time.time())}",
            from_address=from_account.address,
            to_address=to_address,
            amount_wei=amount_wei,
            private_key=from_private_key,
            delegate_chain=[from_account.address, to_address],
            priority=2
        )
        
        self.task_queue.put(task)
        print(f"📋 Created direct transfer: {amount_eth} ETH to {to_address[:10]}...")
        return task
    
    def worker_processor(self, worker: RPCWorker):
        """Worker processing loop"""
        print(f"🔧 Worker {worker.worker_id} started")
        
        while self.is_running:
            try:
                # Get task with timeout
                task = self.task_queue.get(timeout=1)
                
                # Process task
                result = worker.execute_transfer(task)
                
                if result and result.get('status') == 'success':
                    # Record successful transfer
                    record = TransferRecord(
                        tx_hash=result['tx_hash'],
                        from_address=task.from_address,
                        to_address=task.to_address,
                        amount_eth=float(Web3.from_wei(task.amount_wei, 'ether')),
                        gas_used=result['gas_used'],
                        gas_price_gwei=result['gas_price_gwei'],
                        timestamp=time.time(),
                        delegate_chain=task.delegate_chain,
                        status='success'
                    )
                    self.transfer_records.append(record)
                    self.results_queue.put(record)
                    
                    # Update ethics tracker
                    self.ethics.record_transfer(task.from_address, float(Web3.from_wei(task.amount_wei, 'ether')))
                    
                    print(f"✅ Worker {worker.worker_id} completed transfer: {result['tx_hash'][:10]}...")
                else:
                    # Retry logic
                    if task.retry_count < Config.RETRY_ATTEMPTS:
                        task.retry_count += 1
                        self.task_queue.put(task)
                        print(f"🔄 Worker {worker.worker_id} retrying task {task.task_id} (attempt {task.retry_count})")
                    else:
                        print(f"❌ Worker {worker.worker_id} failed task {task.task_id} after {Config.RETRY_ATTEMPTS} attempts")
                
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️ Worker {worker.worker_id} error: {e}")
    
    def start_workers(self):
        """Start all worker threads"""
        threads = []
        for worker in self.workers:
            thread = threading.Thread(target=self.worker_processor, args=(worker,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        return threads
    
    def get_status(self) -> Dict:
        """Get overall system status"""
        worker_stats = [worker.get_stats() for worker in self.workers]
        
        total_tasks = self.task_queue.qsize()
        total_successful = sum(w['successful'] for w in worker_stats)
        total_failed = sum(w['failed'] for w in worker_stats)
        
        return {
            'active_workers': len([w for w in worker_stats if w['connected']]),
            'total_workers': len(self.workers),
            'pending_tasks': total_tasks,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'success_rate': (total_successful / max(1, total_successful + total_failed)) * 100,
            'delegate_chains': len(self.delegate_manager.active_chains),
            'completed_transfers': len(self.transfer_records),
            'worker_details': worker_stats
        }
    
    def stop(self):
        """Stop all workers"""
        self.is_running = False
        print("🛑 Stopping all workers...")

# ==================== LIVE DASHBOARD ====================
class LiveDashboard:
    """Real-time dashboard with curses"""
    
    def __init__(self, manager: WorkerManager):
        self.manager = manager
        self.stdscr = None
        self.auto_mode = False
        
    def run(self):
        """Run live dashboard"""
        try:
            import curses
            self.stdscr = curses.initscr()
            curses.curs_set(0)
            self.stdscr.nodelay(1)
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
            
            while self.manager.is_running:
                self.render()
                self.handle_input()
                time.sleep(0.5)
                    
        except Exception as e:
            print(f"Dashboard error: {e}")
        finally:
            if self.stdscr:
                curses.endwin()
    
    def handle_input(self):
        """Handle keyboard input"""
        try:
            key = self.stdscr.getch()
            if key == ord('q'):
                self.manager.stop()
            elif key == ord('t'):
                self.show_transfers()
            elif key == ord('s'):
                self.show_stats()
        except:
            pass
    
    def render(self):
        """Render dashboard"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Header
        header = f" RPC WORKER FARM - Delegate Chain Transfer System "
        self.stdscr.addstr(0, (width - len(header)) // 2, header, curses.A_BOLD | curses.A_REVERSE)
        
        # Get status
        status = self.manager.get_status()
        
        # Stats Panel
        stats_y = 2
        
        stats_lines = [
            f"ACTIVE WORKERS:     {status['active_workers']}/{status['total_workers']}",
            f"PENDING TASKS:      {status['pending_tasks']}",
            f"SUCCESSFUL TX:      {status['total_successful']}",
            f"FAILED TX:          {status['total_failed']}",
            f"SUCCESS RATE:       {status['success_rate']:.1f}%",
            f"DELEGATE CHAINS:    {status['delegate_chains']}",
            f"COMPLETED TX:       {status['completed_transfers']}",
            f"TARGET ADDRESS:     {Config.TARGET_ADDRESS[:20]}...",
            f"ETHICS MODE:        {'ON' if Config.ETHICS_MODE else 'OFF'}",
        ]
        
        # Draw box
        self.stdscr.addstr(stats_y, 2, "╔══════════════════════════════════════════════════════════════╗")
        self.stdscr.addstr(stats_y+1, 2, "║                    SYSTEM STATUS                           ║")
        self.stdscr.addstr(stats_y+2, 2, "╠══════════════════════════════════════════════════════════════╣")
        
        for i, line in enumerate(stats_lines):
            self.stdscr.addstr(stats_y+3+i, 2, f"║  {line:<62}║")
        
        self.stdscr.addstr(stats_y+13, 2, "╚══════════════════════════════════════════════════════════════╝")
        
        # Worker Panel
        worker_y = stats_y + 15
        self.stdscr.addstr(worker_y, 2, "┌───────────────────── WORKER STATUS ───────────────────────┐")
        
        for i, worker in enumerate(status['worker_details'][:8]):
            if i >= height - worker_y - 3:
                break
            
            status_icon = "✅" if worker['connected'] else "❌"
            line = f"│  {status_icon} Worker {worker['worker_id']}: {worker['tasks_processed']} tasks | {worker['successful']} success | {worker['success_rate']:.0f}%"
            self.stdscr.addstr(worker_y + 1 + i, 2, line.ljust(width-4))
        
        self.stdscr.addstr(worker_y + 10, 2, "└──────────────────────────────────────────────────────────┘")
        
        # Controls Panel
        controls_y = height - 4
        self.stdscr.addstr(controls_y, 2, " Press 't' to view transfers | 's' for stats | 'q' to quit ")
        
        self.stdscr.refresh()
    
    def show_transfers(self):
        """Show recent transfers"""
        print("\n" + "="*60)
        print("                    RECENT TRANSFERS")
        print("="*60)
        
        for record in self.manager.transfer_records[-10:]:
            print(f"\n📦 TX: {record.tx_hash[:20]}...")
            print(f"   From: {record.from_address[:15]}... -> To: {record.to_address[:15]}...")
            print(f"   Amount: {record.amount_eth:.6f} ETH")
            print(f"   Gas: {record.gas_used} | Price: {record.gas_price_gwei:.1f} Gwei")
            print(f"   Chain: {len(record.delegate_chain)} hops")
        
        input("\nPress Enter to continue...")
    
    def show_stats(self):
        """Show detailed statistics"""
        status = self.manager.get_status()
        
        print("\n" + "="*60)
        print("                    DETAILED STATISTICS")
        print("="*60)
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Active Workers: {status['active_workers']}/{status['total_workers']}")
        print(f"   Pending Tasks: {status['pending_tasks']}")
        print(f"   Total Successful: {status['total_successful']}")
        print(f"   Total Failed: {status['total_failed']}")
        print(f"   Success Rate: {status['success_rate']:.2f}%")
        
        print(f"\n🔗 Delegate Chains:")
        print(f"   Active Chains: {status['delegate_chains']}")
        print(f"   Completed Transfers: {status['completed_transfers']}")
        
        print(f"\n⚙️  Worker Details:")
        for worker in status['worker_details']:
            print(f"   Worker {worker['worker_id']}: {worker['tasks_processed']} tasks | {worker['tps']:.1f} tps")
        
        input("\nPress Enter to continue...")

# ==================== MAIN CONTROLLER ====================
class TransferController:
    """Main controller for transfer system"""
    
    def __init__(self):
        self.manager = WorkerManager()
        self.dashboard = LiveDashboard(self.manager)
        
    def start(self):
        """Start the transfer system"""
        print("""
        ╔══════════════════════════════════════════════════════════════╗
        ║         🔥 RPC WORKER FARM - Delegate Chain Transfer         ║
        ║         Multi-Threaded Workers | Ethical Algorithms          ║
        ║         Target: 0x8185d7fEAB5EC3e591eBf7e01F4356be80866598   ║
        ╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Initialize workers
        self.manager.initialize_workers()
        
        if not self.manager.workers:
            print("❌ No workers available")
            return
        
        # Start worker threads
        worker_threads = self.manager.start_workers()
        
        print("\n🎯 System ready!")
        print(f"📡 Target: {Config.TARGET_ADDRESS}")
        print(f"⚙️  Active workers: {len(self.manager.workers)}")
        print(f"🔒 Ethics mode: {'ENABLED' if Config.ETHICS_MODE else 'DISABLED'}")
        print("")
        
        # Interactive menu
        while self.manager.is_running:
            print("\n" + "="*50)
            print("                    COMMANDS")
            print("="*50)
            print("1. Direct Transfer to Target")
            print("2. Delegate Chain Transfer")
            print("3. Show Status")
            print("4. Show Transfers")
            print("5. Launch Dashboard")
            print("6. Exit")
            print("="*50)
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                self.direct_transfer_menu()
            elif choice == '2':
                self.delegate_transfer_menu()
            elif choice == '3':
                status = self.manager.get_status()
                print(f"\n📊 Status: {status['active_workers']} workers | {status['pending_tasks']} pending | {status['total_successful']} success")
            elif choice == '4':
                self.dashboard.show_transfers()
            elif choice == '5':
                self.dashboard.run()
            elif choice == '6':
                self.manager.stop()
                break
            else:
                print("❌ Invalid option")
        
        # Wait for threads
        for thread in worker_threads:
            thread.join(timeout=5)
        
        print("\n✅ System shutdown complete")
    
    def direct_transfer_menu(self):
        """Direct transfer menu"""
        print("\n💰 DIRECT TRANSFER")
        private_key = input("Enter private key: ").strip()
        amount = float(input("Enter amount in ETH: ").strip())
        
        if not private_key or amount <= 0:
            print("❌ Invalid input")
            return
        
        task = self.manager.direct_transfer(private_key, Config.TARGET_ADDRESS, amount)
        if task:
            print(f"✅ Transfer queued: {amount} ETH to {Config.TARGET_ADDRESS}")
    
    def delegate_transfer_menu(self):
        """Delegate chain transfer menu"""
        print("\n🔗 DELEGATE CHAIN TRANSFER")
        private_key = input("Enter private key: ").strip()
        amount = float(input("Enter amount in ETH: ").strip())
        depth = int(input("Delegate chain depth (1-5, default 3): ").strip() or "3")
        
        if not private_key or amount <= 0:
            print("❌ Invalid input")
            return
        
        tasks = self.manager.create_delegate_transfer(private_key, amount, min(depth, 5))
        if tasks:
            print(f"✅ Created {len(tasks)} delegate tasks for {amount} ETH")

# ==================== MAIN ====================
def main():
    controller = TransferController()
    controller.start()

if __name__ == "__main__":
    main()
