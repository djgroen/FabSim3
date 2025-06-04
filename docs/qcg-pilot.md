# QCG Pilot Job installation on remote machines

QCG Pilot Job is a lightweight implementation of the Pilot Job mechanism which
can be used to run a very large number of jobs efficiently on remote clusters and supercomputers.

More information on QCG-PilotJob can be found on their [ReadTheDocs site](https://qcg-pilotjob.readthedocs.io/en/develop/).

<p align="center">
    <img src="../images/qcg-pj.png" alt="Image of a QCG Pilot Job container" width="800" />
</p>
*Example of a QCG-Pilotjob container, which dynamically facilitates a diverse set of code executions within a single queuing system job. [Source](https://link.springer.com/chapter/10.1007/978-3-030-77977-1_39)*

Here we present how you can install QCG Pilot Job on remote machines so that you can use it with FabSim3.

!!! note
    Note that FabSim3 can also work with a pre-installed version of QCG-PilotJob; but for those who need to set it up manually this document is meant to provide some help.

## QCG-PilotJob with FabSim3

QCG-PilotJob is a lightweight workflow manager that efficiently runs large numbers of tasks on HPC systems. It creates a "pilot job" that dynamically schedules and executes your ensemble tasks within a single allocation.

<p align="center">
    <img src="../images/qcg-pj.png" alt="QCG-PilotJob workflow diagram" width="800" />
</p>

*QCG-PilotJob manages multiple tasks within a single job allocation, maximizing resource utilization.*

### Quick Start

#### 1. Setup FabSim3

```bash
git clone https://github.com/djgroen/FabSim3.git
cd FabSim3
python3 configure_fabsim.py
```

> **Note:** Uses your system Python (typically `/usr/bin/python3`) (Recommended)

#### 2. Create Virtual Environment

```bash
fabsim <machine> create_virtual_env
```

#### 3. Install QCG-PilotJob

```bash
fabsim <machine> direct_install_app:QCG-PilotJob,venv=True
```

#### 4. Update Configuration

Add the virtual environment path to your `machines_user.yml`:

```yaml
<machine>:
  virtual_env_path: "/path/to/your/virtual/environment"
```

(e.g., virtual_env_path: "/work/d202/d202/mzr234/VirtualEnv")

#### 5. Test Installation

```bash
fabsim localhost install_plugin:FabDummy
fabsim localhost dummy_ensemble:dummy_test,pj_type=qcg,venv=true
```

### Resource Configuration

Configure your machine resources in `machines_user.yml`:

```yaml
archer2:
  cores: 256            # Total cores to request
  corespernode: 128     # Cores per node (hardware specific)
  cpuspertask: 2        # Cores per individual task
  taskspernode: 64      # Calculated: 128 ÷ 2 = 64
```

This example creates **128 parallel tasks** across **2 nodes**:
- Node 1: 64 tasks × 2 cores = 128 cores
- Node 2: 64 tasks × 2 cores = 128 cores
- Total: 128 tasks using 256 cores

### Usage Examples

#### Basic Ensemble
```bash
fabsim <machine> <app>_ensemble:<config>,pj_type=qcg,venv=true
```

#### With Replicas
```bash
fabsim <machine> <app>_ensemble:<config>,replicas=5,pj_type=qcg,venv=true
```

#### Large Scale Example
```bash
fabsim archer2 dummy_ensemble:dummy_test,replicas=128,cores=256,pj_type=qcg,venv=true
```

#### Custom Resource Allocation
```bash
fabsim <machine> <app>_ensemble:<config>,cores=512,cpuspertask=4,job_wall_time=2:00:00,pj_type=qcg,venv=true
```

### Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `pj_type=qcg` | Enable QCG-PilotJob | Required |
| `venv=true` | Use virtual environment | Recommended |
| `cores=N` | Total cores to allocate | `cores=256` |
| `cpuspertask=N` | Cores per task | `cpuspertask=2` |
| `replicas=N` | Run each task N times | `replicas=10` |
| `job_wall_time=H:M:S` | Maximum job duration | `job_wall_time=4:00:00` |

### Results

Fetch results after completion:
```bash
fabsim <machine> fetch_results
```

Results include:
- Individual task outputs in `RUNS/` subdirectories
- `QCG_PILOT_OUT` file with execution details
- SLURM job logs (`JobID-*.output`, `JobID-*.error`)
- SLRUM logs (`qcg_service.log`, `nl-agent-*.log`)

### Troubleshooting

**Common Issues:**

1. **"QCG not found"** → Check `virtual_env_path` in `machines_user.yml`
2. **Resource allocation errors** → Verify `cpuspertask ≤ corespernode`
3. **Job submission fails** → Check machine-specific SLURM parameters

**Debug Commands:**
```bash
# Check installation
fabsim <machine> direct_install_app:QCG-PilotJob,venv=True

# View job status
fabsim <machine> stat

# Check logs
fabsim <machine> fetch_results
```

### Supported Machines

QCG-PilotJob works on any SLURM-based HPC system. Pre-configured examples:
- ARCHER2 (UK National Supercomputing Service)
- Eagle (NREL HPC)
- Bridges-2 (Pittsburgh Supercomputing Center)

For other machines, configure the SLURM parameters in your machine definition.
