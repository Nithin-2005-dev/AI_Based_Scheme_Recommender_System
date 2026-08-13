import asyncio
import httpx
import time

async def measure_latency():
    url = "http://127.0.0.1:8000/api/docs"
    print("Testing API Latency...")
    times = []
    
    async with httpx.AsyncClient() as client:
        # warm up
        await client.get(url)
        
        for i in range(10):
            start = time.perf_counter()
            res = await client.get(url)
            end = time.perf_counter()
            if res.status_code == 200:
                times.append((end - start) * 1000)
    
    if times:
        avg_ms = sum(times) / len(times)
        min_ms = min(times)
        max_ms = max(times)
        print(f"Latency Results (10 requests):")
        print(f"Average: {avg_ms:.2f} ms")
        print(f"Min: {min_ms:.2f} ms")
        print(f"Max: {max_ms:.2f} ms")
    else:
        print("Failed to reach API.")

if __name__ == "__main__":
    asyncio.run(measure_latency())
