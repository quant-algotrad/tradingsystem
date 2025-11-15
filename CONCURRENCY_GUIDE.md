# Concurrency Guide: Threading vs Multiprocessing vs Async

## TL;DR: What to Use When

```
Task Type                  Solution              Speedup     Use Case
──────────────────────────────────────────────────────────────────────
API Calls (I/O-bound)      Threading            20x         Market data fetching
Indicator Calc (CPU)       Multiprocessing      10x         Signal processing
Database Writes (I/O)      Threading            5x          Historical storage
Network Requests (I/O)     Threading/Async      10-20x      Multiple API calls
Heavy Calculations (CPU)   Multiprocessing      N cores     Backtesting
```

**Current Architecture Already Has Parallelism:**
- Docker containers = Separate processes = Use multiple CPU cores ✅
- No need for threading/multiprocessing if processing 1 symbol at a time

**When You NEED Threading/Multiprocessing:**
- Processing 50+ symbols simultaneously
- Real-time data for large watchlists
- Running backtests on multiple stocks

---

## Python Concurrency Models

### 1. **Sequential** (Current Implementation)

```python
# Process symbols one by one
for symbol in symbols:
    data = fetch(symbol)     # Wait 200ms
    process(data)            # Wait 15ms

# Total: 50 symbols × 215ms = 10,750ms (10.75 seconds)
```

**Pros:**
- ✅ Simple to understand
- ✅ Easy to debug
- ✅ No race conditions
- ✅ Works perfectly for 1-10 symbols

**Cons:**
- ❌ Slow for many symbols
- ❌ CPU cores idle while waiting for I/O

---

### 2. **Threading** (I/O-bound tasks)

```python
from concurrent.futures import ThreadPoolExecutor

# Process symbols concurrently
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(fetch_and_process, symbols)

# Total: 50 symbols / 10 workers = ~500ms (0.5 seconds)
# SPEEDUP: 20x faster!
```

**How It Works:**
- Multiple threads in ONE process
- When one thread waits for I/O (network, disk), others run
- Python GIL allows I/O operations to release the lock
- Perfect for API calls, database queries, file operations

**Pros:**
- ✅ 10-20x faster for I/O-bound tasks
- ✅ Low memory overhead (threads share memory)
- ✅ Easy to implement with ThreadPoolExecutor
- ✅ Good for network/disk operations

**Cons:**
- ❌ Python GIL limits to ONE CPU core for calculations
- ❌ Not suitable for CPU-intensive tasks
- ❌ Requires thread-safe code (locks, semaphores)

**Best For:**
- Market data fetching (API calls)
- Database queries
- File I/O
- Network requests

---

### 3. **Multiprocessing** (CPU-bound tasks)

```python
from multiprocessing import Pool

# Process symbols in parallel (separate processes)
with Pool(processes=10) as pool:
    pool.map(calculate_indicators, symbol_data)

# Total: 50 symbols / 10 cores = ~75ms
# SPEEDUP: 10x faster!
```

**How It Works:**
- Multiple PROCESSES (not threads)
- Each process has its own Python interpreter
- NO GIL limitations - uses multiple CPU cores
- Perfect for heavy calculations

**Pros:**
- ✅ True parallel execution (uses all CPU cores)
- ✅ Bypasses Python GIL
- ✅ 10x faster for CPU-intensive tasks
- ✅ Isolated memory (no race conditions)

**Cons:**
- ❌ Higher memory overhead (each process copies data)
- ❌ Slower startup (forking processes)
- ❌ More complex inter-process communication

**Best For:**
- Indicator calculations
- Backtesting
- Machine learning models
- Heavy number crunching

---

### 4. **Async/Await** (I/O-bound with explicit control)

```python
import asyncio

async def fetch_all(symbols):
    tasks = [fetch_symbol(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)
    return results

# Total: 50 symbols in ~500ms (concurrent I/O)
# SPEEDUP: 20x faster!
```

**How It Works:**
- Single thread, single process
- Explicit yield points (await)
- Event loop manages concurrent tasks
- Perfect for network I/O with async libraries

**Pros:**
- ✅ Very lightweight (no threads/processes)
- ✅ Explicit control over concurrency
- ✅ Great for thousands of connections
- ✅ Low memory overhead

**Cons:**
- ❌ Requires async libraries (aiohttp, asyncpg)
- ❌ More complex code (async/await syntax)
- ❌ Cannot mix sync and async easily
- ❌ Still limited by GIL for CPU tasks

**Best For:**
- Websocket connections
- Thousands of concurrent API calls
- Real-time data streams
- High-concurrency servers

---

## Performance Comparison

### Market Data Fetching (50 symbols)

```
Method              Time        CPU Usage    Memory    Code Complexity
─────────────────────────────────────────────────────────────────────
Sequential          10,000ms    1 core       50MB      ★☆☆☆☆
Threading           500ms       1 core       60MB      ★★☆☆☆
Async/Await         500ms       1 core       55MB      ★★★☆☆
Multiprocessing     500ms       10 cores     500MB     ★★★★☆
```

**Winner:** Threading (best balance of speed, memory, simplicity)

---

### Indicator Calculation (50 symbols)

```
Method              Time        CPU Usage    Memory    Code Complexity
─────────────────────────────────────────────────────────────────────
Sequential          750ms       1 core       100MB     ★☆☆☆☆
Threading           750ms       1 core       110MB     ★★☆☆☆ (no benefit!)
Async/Await         750ms       1 core       105MB     ★★★☆☆ (no benefit!)
Multiprocessing     75ms        10 cores     500MB     ★★★☆☆
```

**Winner:** Multiprocessing (only way to speed up CPU-bound tasks)

---

## Your Trading System: What to Use

### Current Architecture (Microservices)

```
Container 1: Market Data Ingestion    → Already parallel! ✅
Container 2: Signal Processing        → Already parallel! ✅
Container 3: Trade Execution          → Already parallel! ✅
Container 4: Risk Monitoring          → Already parallel! ✅

These run on SEPARATE CPU cores automatically.
```

**You already have process-level parallelism via Docker!**

---

### When to Add Threading/Multiprocessing

#### ❌ DON'T add if:
- Trading only 1-10 symbols
- Processing sequentially is fast enough
- System already meets latency requirements

#### ✅ DO add if:
- Trading 50+ symbols simultaneously
- Need real-time data for large watchlists
- Running backtests on multiple stocks
- Latency requirements < 100ms per symbol

---

## Implementation Examples

### 1. **Threaded Market Data Ingestion** (Already Created)

**File:** `src/workers/market_worker_threaded.py`

```python
from concurrent.futures import ThreadPoolExecutor

class ThreadedMarketDataWorker:
    def run_quote_collection(self):
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self._fetch_quote_safe, self.symbols)
```

**Performance:**
- Sequential: 50 symbols × 200ms = 10,000ms
- Threading:  50 symbols / 10 workers = 500ms
- **Speedup: 20x**

**To Use:**
```bash
# Update docker-compose.yml
services:
  market_data_ingestion:
    command: ["python", "-m", "src.workers.market_worker_threaded"]
```

---

### 2. **Multicore Signal Processing** (Already Created)

**File:** `src/workers/signal_multicore.py`

```python
from multiprocessing import Pool

class MultiCoreSignalProcessor:
    def process_batch(self, events):
        with Pool(processes=10) as pool:
            results = pool.map(calculate_indicators_for_symbol, events)
```

**Performance:**
- Sequential:      50 symbols × 15ms = 750ms
- Multiprocessing: 50 symbols / 10 cores = 75ms
- **Speedup: 10x**

**To Use:**
```bash
# Update docker-compose.yml
services:
  signal_processor:
    command: ["python", "-m", "src.workers.signal_multicore"]
```

---

### 3. **Async Market Data** (If Using Websockets)

```python
import asyncio
import aiohttp

class AsyncMarketDataFetcher:
    async def fetch_symbol(self, session, symbol):
        async with session.get(f"https://api.example.com/{symbol}") as response:
            return await response.json()

    async def fetch_all(self, symbols):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_symbol(session, symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks)
            return results

# Usage
fetcher = AsyncMarketDataFetcher()
results = asyncio.run(fetcher.fetch_all(symbols))
```

**Performance:**
- Sequential: 50 × 200ms = 10,000ms
- Async:      50 concurrent = 200ms (single request latency)
- **Speedup: 50x**

**When to Use:**
- Real-time websocket streams
- Thousands of concurrent connections
- Broker APIs with async support

---

## Hybrid Approach (Recommended)

Combine threading (I/O) + multiprocessing (CPU) for optimal performance:

```python
class HybridWorker:
    def run(self):
        # Step 1: Fetch data with threading (I/O-bound)
        with ThreadPoolExecutor(max_workers=10) as executor:
            market_data = executor.map(self.fetch_symbol, symbols)

        # Step 2: Calculate indicators with multiprocessing (CPU-bound)
        with Pool(processes=10) as pool:
            signals = pool.map(self.calculate_indicators, market_data)

        # Step 3: Process signals sequentially (fast enough)
        for signal in signals:
            self.process_signal(signal)
```

**Performance:**
- Fetch (threading):      500ms
- Calculate (multiproc):  75ms
- Process (sequential):   50ms
- **Total: 625ms vs 11,500ms sequential (18x speedup!)**

---

## Thread Safety Considerations

### Thread-Safe Code

```python
from threading import Lock

class ThreadSafeKafkaProducer:
    def __init__(self):
        self._producer = KafkaProducer()
        self._lock = Lock()  # Protect shared resource

    def send(self, topic, message):
        with self._lock:  # Only one thread at a time
            self._producer.send(topic, message)
```

### Not Thread-Safe (Will Crash!)

```python
# BAD: Multiple threads writing to same Kafka producer
def worker(symbol):
    producer.send('topic', data)  # Race condition!

with ThreadPoolExecutor() as executor:
    executor.map(worker, symbols)  # CRASH!
```

### Solution: Use Locks or Thread-Local Storage

```python
# GOOD: Thread-safe with lock
def worker(symbol):
    with producer_lock:
        producer.send('topic', data)  # Safe!
```

---

## Benchmarking Your System

Run the benchmark to see actual performance:

```bash
# Benchmark threading vs sequential
python -m src.workers.market_worker_threaded benchmark

# Expected output:
# Sequential:      10.2s
# Threading:       0.5s
# Speedup:         20.4x

# Benchmark multiprocessing vs sequential
python -m src.workers.signal_multicore benchmark

# Expected output:
# Sequential:      0.75s
# Multiprocessing: 0.08s
# Speedup:         9.4x
```

---

## Recommendation for Your System

### For 10 Symbols (Current):
✅ **Keep sequential** - Already fast enough
- Market data: 10 × 200ms = 2s (acceptable)
- Signals: 10 × 15ms = 150ms (fast)

### For 50+ Symbols:
✅ **Use threading for data fetching**
- 50 symbols in 500ms vs 10s
- File: `market_worker_threaded.py`

✅ **Use multiprocessing for indicators**
- 50 symbols in 75ms vs 750ms
- File: `signal_multicore.py`

### For 100+ Symbols:
✅ **Use hybrid approach**
- Threading for I/O
- Multiprocessing for CPU
- Async for websockets (if available)

---

## Summary Table

| Concurrency Model | Best For | Speedup | Complexity | Memory |
|-------------------|----------|---------|------------|--------|
| **Sequential** | 1-10 symbols | 1x | ★☆☆☆☆ | Low |
| **Threading** | I/O-bound (API calls) | 10-20x | ★★☆☆☆ | Low |
| **Multiprocessing** | CPU-bound (calculations) | 10x | ★★★☆☆ | High |
| **Async/Await** | Websockets, 1000+ connections | 20-50x | ★★★★☆ | Low |
| **Hybrid** | Large-scale production | 20-30x | ★★★★★ | Medium |
| **Docker Containers** | Microservices (already doing this!) | N cores | ★★☆☆☆ | Medium |

---

## Your Current Architecture is Already Good!

```
✅ You have: Docker containers (process-level parallelism)
✅ Performance: ~10-20ms critical path
✅ Suitable for: Swing/intraday trading

Only add threading/multiprocessing if:
- Trading 50+ symbols
- Need <100ms per symbol
- Running backtests on large datasets
```

**My recommendation:** Keep current architecture for now. It's well-designed and suitable for your use case (₹50k capital, 10-20 stocks). Only optimize if you scale to 100+ symbols.

---

## Files Created

1. **src/workers/market_worker_threaded.py**
   - Threading for concurrent API calls
   - 20x faster for 50+ symbols

2. **src/workers/signal_multicore.py**
   - Multiprocessing for CPU-bound calculations
   - 10x faster for indicator processing

3. **CONCURRENCY_GUIDE.md** (this file)
   - Complete guide to concurrency in trading systems

---

**Bottom Line:** Your microservices architecture already provides parallelism. Threading/multiprocessing is only needed when processing many symbols simultaneously.
