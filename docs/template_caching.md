# Template Caching Performance Feature

FabSim3 includes an intelligent template caching system that dramatically improves performance for large ensemble jobs, providing **8-11x speedup** with minimal memory overhead. This feature optimizes the template processing pipeline that generates job scripts for HPC systems.

## Overview

### How It Works

FabSim3's template caching uses a **two-tier architecture**:

1. **Raw Template Cache**: Shared across all jobs - caches template file content to eliminate repeated disk I/O
2. **Processed Template Cache**: Environment-aware - caches processed templates based on unique variable combinations

### Performance Benefits

- **Individual templates**: 8-11x speedup for template processing
- **Ensemble jobs**: 91% performance improvement for 100+ replicas  
- **Large ensembles**: Time savings scale with job size
- **Memory efficient**: Typical usage ~2-10MB RAM

## Configuration

### 1. machines_user.yml Configuration (Recommended)

```yaml
# FabSim3/fabsim/deploy/machines_user.yml
default:
  # Global default for all machines
  enable_template_cache: true
  template_cache_size: 2000        # Number of processed template entries

localhost:
  username: myuser
  enable_template_cache: true      # Enable for local testing
  template_cache_size: 5000        # Larger cache for development

archer2:
  username: myuser
  enable_template_cache: true      # Recommended for HPC
  template_cache_size: 10000       # Large cache for big ensemble jobs
```

### 2. Environment Variables (Quick Testing)

```bash
# Enable/disable caching
export ENABLE_TEMPLATE_CACHE=true   # or false

# Set cache size (number of entries, not MB!)
export TEMPLATE_CACHE_SIZE=5000

# Run with custom settings
ENABLE_TEMPLATE_CACHE=false fabsim localhost dummy_ensemble:test,replicas=100
```

### 3. Configuration Priority (Highest to Lowest)

1. **Environment variables** (`ENABLE_TEMPLATE_CACHE`, `TEMPLATE_CACHE_SIZE`)
2. **Machine-specific settings** (e.g., `localhost:` section in machines_user.yml)
3. **Global defaults** (`default:` section in machines_user.yml)
4. **Built-in defaults** (enabled, size=2000)

## Cache Size Guidelines

### Understanding Cache Size

**Important**: `template_cache_size: 2000` means **2000 cache entries**, NOT megabytes!

- Each entry stores one processed template variant
- Memory usage: ~1-5KB per entry
- Total memory: 2000 entries ≈ 2-10MB RAM

### Recommended Sizes by Job Type

| Job Type | Replicas | Recommended Cache Size | Memory Usage |
|----------|----------|------------------------|--------------|
| **Small** | < 100 | 1,000 - 2,000 | ~1-10 MB |
| **Medium** | 100-1,000 | 5,000 - 10,000 | ~5-50 MB |
| **Large** | 1,000+ | 10,000 - 50,000 | ~50-250 MB |
| **Extreme** | 10,000+ | 100,000+ | ~500MB - 5GB |

### Cache Size Limitations

**No hard upper limit** - only limited by available RAM  
**Minimum recommended**: 100+ entries  
**Avoid**: Size 0 (disables cleanup, causes memory growth)

## Performance Benchmarks

### Real-world Results

```bash
# Ensemble simulation (100 replicas)
Without caching: 0.0103 seconds
With caching:    0.0009 seconds
Speedup:         11.27x (91.1% improvement)

# Individual template performance:
qcg-PJ-header:   8.0x speedup (87.5% improvement)
qcg-PJ-py:      10.2x speedup (90.2% improvement)  
bash_header:     8.6x speedup (88.3% improvement)
```

### Scaling Estimates

- **Time saved per replica**: ~0.09 ms
- **1,000 replicas**: ~0.1 seconds saved
- **10,000 replicas**: ~0.9 seconds saved

> **Note**: Benefits increase significantly for template-heavy workflows

## Advanced Usage

### Programmatic Control

```python
from fabsim.deploy.templates import (
    set_template_caching, 
    get_template_cache_stats,
    clear_template_cache,
    benchmark_template_performance
)

# Enable/disable caching
set_template_caching(True)

# Get detailed cache statistics
stats = get_template_cache_stats()
print(f"Caching enabled: {stats['caching_enabled']}")
print(f"Raw templates cached: {stats['raw_templates_cached']}")
print(f"Processed templates cached: {stats['processed_templates_cached']}")
print(f"Cache hit ratio: {stats['cache_hit_ratio']}")
print(f"Memory usage: {stats['memory_usage_estimate']} bytes")

# Clear cache (for testing)
clear_template_cache()

# Benchmark specific template
results = benchmark_template_performance("qcg-PJ-header", iterations=100)
print(f"Speedup: {results['speedup_factor']}x")
print(f"Efficiency: {results['cache_efficiency']}")
```

### Monitoring Cache Performance

Check if caching is working effectively:

```python
# Run your ensemble job, then check cache stats
stats = get_template_cache_stats()

# Good indicators:
print(f"Cache hit ratio: {stats['cache_hit_ratio']}")       # Should be high (>80%)
print(f"Templates cached: {stats['processed_templates_cached']}")  # Should grow with job size
print(f"Memory usage: {stats['memory_usage_estimate']/1024/1024:.1f} MB")  # Should be reasonable
```

## Technical Architecture

### Cache Scope & Sharing

**Raw Template Cache**:

- **Scope**: Global across all jobs and processes
- **Purpose**: Eliminate redundant file I/O operations
- **Sharing**: Template files read once, used everywhere

**Processed Template Cache**:

- **Scope**: Per unique environment variable combination
- **Purpose**: Avoid redundant template processing  
- **Cache Key**: `(template_name, frozenset(relevant_env_vars))`

### Cache Lifecycle

- **Location**: Process RAM (not disk storage)
- **Persistence**: Per FabSim execution (cleared when process ends)
- **Multiprocessing**: Each worker process has separate cache
- **Cleanup**: FIFO eviction when cache size limit reached

### Memory Management

When cache reaches `template_cache_size` limit:

- Remove oldest 10% of entries
- Always remove at least 1 entry
- Prevents unbounded memory growth
- Raw template cache never cleared

## Status Reporting

FabSim3 displays cache status during job preparation:

```text
╭──────── job preparation phase ────────╮
│ tmp_work_path = /tmp/abc123/FabSim3   │
│ Template cache: ENABLED               │
╰───────────────────────────────────────╯
```

## Troubleshooting

### Common Issues

**Multiple cache notifications**: Fixed in recent versions  
**Cache not working**: Check `enable_template_cache: true` in config  
**High memory usage**: Reduce `template_cache_size` value  
**Configuration errors**: Check logs for invalid numeric values  

### Debugging

```bash
# Test with caching disabled
ENABLE_TEMPLATE_CACHE=false fabsim localhost dummy_test

# Compare performance
time fabsim localhost dummy_ensemble:test,replicas=50  # with cache
ENABLE_TEMPLATE_CACHE=false time fabsim localhost dummy_ensemble:dummy_test,replicas=50  # without cache
```

## Best Practices

### Production Recommendations

**Enable caching** for all production ensemble jobs  
**Use larger cache sizes** for big ensemble jobs (10,000+ entries)  
**Monitor memory usage** when using very large caches  
**Test your workload** to find optimal cache size  

### Research & Benchmarking

**Disable caching** when comparing algorithm performance  
**Use environment variables** for quick testing  
**Document cache settings** in research papers  
**Benchmark your specific templates** for accurate performance data  

## Migration Notes

If upgrading from previous FabSim3 versions:

- Template caching is **enabled by default** (was disabled before)
- Cache status now shows in job preparation phase (cleaner output)  
- No breaking changes to existing configurations
- Previous `ENABLE_TEMPLATE_CACHE` environment variable still works

This intelligent caching system makes FabSim3 exceptionally fast for large ensemble jobs while maintaining complete flexibility for research and debugging purposes.
