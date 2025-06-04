# SLURM Pilot Jobs with FabSim3

FabSim3 provides native SLURM-based pilot job implementations that leverage SLURM's built-in capabilities without requiring additional software installations.

## Quick Start

### 1. Configure Machine Resources

Add SLURM parameters to your `machines_user.yml`:

```yaml
archer2:
  username: your_username
  cores: 256            # Total cores to request
  corespernode: 128     # Hardware cores per node
  cpuspertask: 2        # Cores per individual task
  taskspernode: 64      # Calculated: 128 ÷ 2 = 64
```

### 2. Run Your Ensemble

```bash
# SLURM Job Arrays (recommended for < 1000 tasks)
fabsim <machine> <app>_ensemble:<config>,pj_type=slurm-array

# SLURM Manager (recommended for > 1000 tasks)
fabsim <machine> <app>_ensemble:<config>,pj_type=slurm-manager
```

## Two SLURM Approaches

### SLURM Job Arrays (`pj_type=slurm-array`)

**Best for:** Independent tasks, fault tolerance, mixed durations

Each task becomes a separate SLURM job within a job array.

**Advantages:**
- ✅ Independent execution (one failure doesn't affect others)
- ✅ Full wall time per task
- ✅ Better for long-running tasks

**Limitations:**
- ❌ Limited by SLURM array size (typically 1000-32000)
- ❌ Uses multiple scheduler slots

### SLURM Manager (`pj_type=slurm-manager`)

**Best for:** Large ensembles, uniform tasks, resource efficiency

Single SLURM job that internally manages multiple tasks.

**Advantages:**
- ✅ No array size limitations
- ✅ Single scheduler slot
- ✅ Efficient resource utilization

**Limitations:**
- ❌ All tasks fail if main job fails
- ❌ Shared wall time across tasks

## Usage Examples

### Basic Examples

```bash
# Small parameter sweep (50 tasks)
fabsim archer2 dummy_ensemble:dummy_test,pj_type=slurm-array

# Large Monte Carlo study (5000 tasks)
fabsim archer2 dummy_ensemble:monte_carlo,pj_type=slurm-manager

# Custom resource allocation
fabsim archer2 dummy_ensemble:config,cores=512,cpuspertask=4,pj_type=slurm-array
```

### Advanced Configuration

```yaml
# In machines_user.yml
archer2:
  # Basic SLURM config
  cores: 256
  corespernode: 128
  cpuspertask: 2
  taskspernode: 64
  
  # Advanced options
  max_concurrent: 20        # For manager mode
```

## Choosing the Right Approach

| Scenario | Task Count | Duration | Recommended |
|----------|------------|----------|-------------|
| Parameter sweep | < 100 | Mixed | `slurm-array` |
| Monte Carlo | > 1000 | Uniform | `slurm-manager` |
| Long simulations | Any | > 2 hours | `slurm-array` |
| Quick analysis | > 100 | < 30 min | `slurm-manager` |

**Auto-selection:** If you don't specify `pj_type`, FabSim3 automatically chooses based on task count and system limits.

## System Limits and Information

Before choosing your approach, check your system's capabilities:

```bash
# Check current array limits
scontrol show config | grep -i array
# Typical output: MaxArraySize=32001

# Check queue limits and node information
sinfo -o "%P %l %D %c %m %a %S"
# Shows: Partition, TimeLimit, Nodes, CPUs, Memory, Availability, NodeSize
```

## Monitoring Jobs

### SLURM Arrays
```bash
# View all array jobs
squeue -u $USER

# Cancel specific array task
scancel JOBID_TASKID

# Cancel entire array
scancel JOBID
```

### SLURM Manager
```bash
# View manager job
squeue -u $USER -j JOBID

# Monitor progress
tail -f results/manager_output.log

# Cancel manager
scancel JOBID
```

## Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `pj_type=slurm-array` | Use SLURM job arrays | For < 1000 tasks |
| `pj_type=slurm-manager` | Use SLURM manager | For > 1000 tasks |
| `cores=N` | Total cores to allocate | `cores=256` |
| `cpuspertask=N` | Cores per task | `cpuspertask=2` |
| `max_concurrent=N` | Parallel tasks (manager) | `max_concurrent=20` |

## Troubleshooting

**Common Issues:**

1. **Array size exceeded** → Use `slurm-manager` instead
2. **Resource allocation errors** → Check `cpuspertask ≤ corespernode`
3. **Tasks timing out** → Increase `job_wall_time` or `task_timeout`

**Debug Commands:**
```bash
# Check SLURM limits
scontrol show config | grep -i array

# Test configuration
fabsim <machine> stat

# View detailed logs
fabsim <machine> fetch_results
```

## Performance Comparison

Example on ARCHER2 (256 cores, 2 nodes):

| Approach | Tasks | Completion Time | Efficiency |
|----------|-------|-----------------|------------|
| `slurm-array` | 100 × 30min | 30 minutes | 85% |
| `slurm-manager` | 100 × 30min | 15 minutes | 95% |
| `slurm-array` | 1000 × 10min | 2 hours | 60% |
| `slurm-manager` | 1000 × 10min | 45 minutes | 90% |

**Key Takeaway:** SLURM manager is generally more efficient for large numbers of uniform tasks, while arrays are better for fault tolerance and mixed workloads.
