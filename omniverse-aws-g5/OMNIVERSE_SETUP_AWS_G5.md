# OMNIVERSE SET UP

_NextEra Energy — AWS G5 + NVIDIA Omniverse (demo deck in Markdown)_  
_Template: Omniverse Set-Up-demo.pptx_

---

## Slide 1 — Title

# OMNIVERSE  
## SET UP

AWS G5 · NVIDIA A10G · Omniverse Kit

**Speaker notes**

Hello everyone.  
In this session we walk through how NVIDIA Omniverse is set up in the cloud. This is a demonstration — you do not need to install or configure anything.  
By the end you will understand how GPU quota, the G5 instance, drivers, CUDA, and Kit fit together.

---

## Slide 2 — Agenda

# AGENDA

1. Requesting GPU quota  
2. Launch virtual machine (Azure vs AWS G5)  
3. NVIDIA GPU driver  
4. CUDA Toolkit  
5. Omniverse Kit  

**Speaker notes**

GPU quota cannot be created by Terraform, CloudFormation, or Bicep. It is a manual portal request per region.  
Instances for this cohort are already prepared. We focus on the environment, the install path, and how components work together.

---

## Slide 3 — Requesting quota increase

# REQUESTING QUOTA INCREASE

GPU quota is a **mandatory** step. Without it, Launch Instance fails with a vCPU limit error.

### AWS (target for this engagement)

| Item | Value |
|------|--------|
| Family | **G5** — NVIDIA **A10G** Tensor Core (24 GB VRAM) |
| Quota name | **Running On-Demand G and VT instances** |
| Unit | **vCPUs per Region** (not “number of VMs”) |
| Default | Often **0** on a new account |
| Where | AWS Console → **Service Quotas** → **Amazon EC2** |
| Filter | `On-Demand` + `G and VT` |
| Do not use | Spot quota (`All G and VT Spot Instance Requests`) — it will not launch On-Demand G5 |

Recommended request (demo / workstation):

| Use case | Instance | vCPUs to request | Why |
|----------|----------|------------------|-----|
| Kit smoke test | `g5.2xlarge` | **8** (+ buffer) | Minimum comfortable Windows + Kit |
| RTX workstation (preferred) | `g5.4xlarge` | **16** | Closest AWS match to Azure `Standard_NV18ads_A10_v5` |
| Heavy USD / multi-viewport | `g5.8xlarge` | **32** | More host RAM and EBS/network |

Always request **current usage + planned G5 vCPUs + 10–30% buffer**, in the **same Region** where you will launch.

### Azure (template parallel)

| Item | Value |
|------|--------|
| VM size | `Standard_NV18ads_A10_v5` |
| Need | **18 vCPUs** in the NV A10 v5 family |
| Where | Azure Portal → **Quotas** → Compute |
| Filter | `nvadsa10v5` · Region e.g. **East US** |

**Speaker notes**

Quota is regional. Approving G5 in `us-east-1` does nothing for `us-west-2`.  
G5 is not available in every AZ (example: historically weak in `us-west-1`). Pick a Region that has G5 capacity before you file the ticket.

---

## Slide 4 — Section: Launch virtual machine

# LAUNCH VIRTUAL MACHINE

Two clouds, one GPU class: **NVIDIA Ampere A10 / A10G** for RTX.

---

## Slide 5 — Launch Azure virtual machine (context)

# LAUNCH AZURE VIRTUAL MACHINE

Connect to the virtual machine over **RDP**.

Typical training SKU from the template:

- Size: `Standard_NV18ads_A10_v5`  
- GPU: NVIDIA **A10**  
- OS: Windows 11 Pro/Enterprise image  
- Access: RDP **3389** only from corporate CIDR  

---

## Slide 6 — Azure vs AWS mapping

# LAUNCH AZURE VIRTUAL MACHINE

| Azure | AWS G5 equivalent |
|-------|-------------------|
| `Standard_NV18ads_A10_v5` (18 vCPU, A10) | **`g5.4xlarge`** (16 vCPU, 64 GiB, **1× A10G 24 GB**) |
| Resource group + VNet + NSG | VPC + subnet + **Security Group** (+ optional NACL) |
| Public IP + NIC | Elastic IP (only if required) + ENI |
| NVIDIA GPU Driver **Extension** | AWS **GRID / RTX vWS** driver (or NVIDIA install) |
| Quota: NV family vCPUs | Quota: **G and VT** On-Demand vCPUs |

A10 vs A10G: same Ampere generation, 24 GB; A10G is the AWS data-center SKU. RTX in Omniverse is supported on both.

---

## Slide 7 — Launch AWS instance

# LAUNCH AWS INSTANCE

### G5 family (NVIDIA A10G)

| Instance | GPUs | vCPU | RAM | Local NVMe | When to use |
|----------|------|------|-----|------------|-------------|
| `g5.xlarge` | 1 | 4 | 16 GiB | 250 GB | Too tight for Windows + Kit — avoid |
| **`g5.2xlarge`** | 1 | 8 | 32 GiB | 450 GB | Demo / Kit launch |
| **`g5.4xlarge`** | 1 | 16 | 64 GiB | 600 GB | **Recommended workstation** |
| `g5.8xlarge` | 1 | 32 | 128 GiB | 900 GB | Large USD assemblies |
| `g5.16xlarge` | 1 | 64 | 256 GiB | 1900 GB | Single GPU, max host RAM |
| `g5.12xlarge` | 4 | 48 | 192 GiB | 3800 GB | Multi-GPU (not needed for first Kit) |
| `g5.24xlarge` | 4 | 96 | 384 GiB | 3800 GB | Farm / batch |
| `g5.48xlarge` | 8 | 192 | 768 GiB | 7600 GB | Max A10G density |

### Launch checklist (EC2 console)

1. **AMI**  
   - Default marketplace: **Windows Server 2022/2025**.  
   - **Windows 11** is not a stock G5 AMI — import a custom VHD/AMI (BYOL) if the customer mandates Win11.  
   - Linux/headless Kit or Isaac: NVIDIA Omniverse GPU-Optimized AMI (`g5.2xlarge`+).
2. **Instance type:** `g5.4xlarge` (preferred) or `g5.2xlarge`.  
3. **Subnet:** private preferred; jump host or VPN for RDP.  
4. **Storage:** gp3 root **≥ 256 GB** (Kit + CUDA + USD). Instance store is ephemeral — do not put projects only there.  
5. **IAM:** SSM Session Manager role if you want console access without opening 3389 to the internet.  
6. **Key pair:** required for Windows password decrypt (unless SSM + AD).

**Speaker notes**

We select the G5 family because it provides NVIDIA GPUs with RTX support.  
AWS provides Windows **Server** images by default. Windows 11 needs a custom import.  
**Security Groups** apply at the instance (ENI). **NACLs** apply at the subnet — use SG as the primary control, NACL as a coarse extra layer.

---

## Slide 8 — Launch AWS instance (network & drivers)

# LAUNCH AWS INSTANCE

### Security Group (instance)

| Direction | Port | Source | Purpose |
|-----------|------|--------|---------|
| Inbound | TCP **3389** | Corporate CIDR only | RDP |
| Inbound | TCP **22** | Bastion / VPN only | Linux SSH (if used) |
| Inbound | TCP **443** | VPC / VPN | Nucleus / HTTPS if co-located |
| Outbound | HTTPS **443** | `0.0.0.0/0` | CUDA, NGC, GitHub, Windows Update |

Never open RDP to `0.0.0.0/0`. Prefer **VPN / Direct Connect + private IP**.

### Drivers on G5

Two valid paths:

1. **AWS GRID driver** (recommended for Windows RTX / Omniverse desktop).  
   Follow [Install NVIDIA drivers on Windows](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/install-nvidia-driver.html) for **G5**.  
2. **Manual NVIDIA package** inside the OS (same idea as the Azure “optional local install” slide).

AWS also publishes PowerShell helpers for a fast GRID install; reboot after install.

**Speaker notes**

Access is controlled by the Security Group: which ports, and who may connect.  
Drivers: AWS PowerShell scripts for a quick GRID setup, or a manual NVIDIA install as shown later.

---

## Slide 9 — GPU driver path

# LAUNCH VIRTUAL MACHINE WITH NVIDIA GPU DRIVER

| Cloud | Mechanism |
|-------|-----------|
| Azure | VM extension **NVIDIA GPU Driver** (`Microsoft.HpcCompute` / `NvidiaGpuDriverWindows`) |
| AWS G5 | **GRID / RTX Virtual Workstation** driver for graphics + RTX |

Azure SKU in the original deck: `Standard_NV18ads_A10_v5` — gen-5 A10, RTX-capable.  
AWS SKU for the same class of work: **`g5.4xlarge`**.

**Speaker notes**

`Standard_NV18ads_A10_v5` is a generation-5 VM on NVIDIA A10, suitable for RTX rendering. G5 A10G is the AWS counterpart.

---

## Slide 10 — NVIDIA GPU driver

# NVIDIA GPU DRIVER

Optional / parallel path: install the NVIDIA GPU driver **inside** the VM (not only via Azure extension).

On AWS: after GRID install, reboot, then verify with `nvidia-smi`.

**Speaker notes**

This is the optional in-guest driver path.

---

## Slide 11 — Install NVIDIA driver and verify

# INSTALL NVIDIA DRIVER

Use the **NVIDIA / AWS GRID driver first**, then confirm with **`nvidia-smi`**.

### Verify

1. RDP to the instance.  
2. Open **Command Prompt** or **PowerShell as Administrator**.  
3. Run:

```bat
cd "C:\Program Files\NVIDIA Corporation\NVSMI"
nvidia-smi
```

If `NVSMI` is not on that path (newer driver layouts):

```bat
nvidia-smi
```

### Expected

- GPU name: **NVIDIA A10G** (AWS) or **A10** (Azure)  
- Driver version listed  
- Persistence / `GPU-Util` may be `N/A` or `0%` with no workload — that is normal  

If `nvidia-smi` fails: wrong driver branch (Tesla compute-only vs GRID graphics), incomplete install, or no reboot.

---

## Slide 12 — Section: CUDA Toolkit

# Install CUDA TOOLKIT

---

## Slide 13 — Install CUDA Toolkit

# INSTALL CUDA TOOLKIT

CUDA Toolkit is required for RTX rendering, physics, and GPU compute workloads.

**Prerequisite:** NVIDIA account (sign-in required to download the package).

### Download

1. Open the CUDA downloads page (Windows, x86_64, Windows 11 **or** Windows Server, **exe (local)**).  
2. Download **CUDA Toolkit 13.2** (same pin as the demo template).  
3. Run the installer as Administrator. Reboot if requested.

### Reference

[CUDA Toolkit downloads](https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local)

**Speaker notes**

Download is a manual browser action (NVIDIA login). Do not expect this step in IaC.

---

## Slide 14 — CUDA on the instance

# INSTALL CUDA TOOLKIT

After install, confirm compiler and driver still agree:

```bat
nvidia-smi
where nvcc
nvcc --version
```

Keep **one** known-good combo: **G5 GRID driver + CUDA 13.2 + Kit build**. Do not mix random Game Ready drivers on a cloud GPU.

---

## Slide 15 — Section: Omniverse Kit

# Omniverse Kit

---

## Slide 16 — Launch Omniverse Kit

# LAUNCH OMNIVERSE KIT

### Clone NVIDIA Omniverse kit app

Clone `NVIDIA-Omniverse/kit-app-template` from GitHub:

```bat
git clone https://github.com/NVIDIA-Omniverse/kit-app-template.git
cd kit-app-template
```

### Create a new application from template

```bat
.\repo.bat template new
```

### Build

```bat
.\repo.bat build
```

### Launch

```bat
.\repo.bat launch
```

Requires **Git for Windows** and a working GPU driver (`nvidia-smi` OK) before first launch.

---

## Slide 17 — Kit first-run wizard

# LAUNCH OMNIVERSE KIT

Complete the **initial setup** of the Kit application:

1. Accept **license and consent**.  
2. **Create Application**.  
3. Set:  
   - application name  
   - `.kit` file name  
   - display name  
   - application version  
4. Leave remaining options at defaults for the first setup.

**Speaker notes**

This is the first-run template wizard. Defaults are recommended for a first successful launch.

---

## Slide 18 — Kit running

# LAUNCH OMNIVERSE KIT

UI load confirms:

- the application was **created successfully**  
- the **Kit runtime** is working  
- the environment is ready for **USD scenes, extensions, and RTX**  
- next step: connect to **Enterprise Nucleus** for collaboration  

**Speaker notes**

From here we work with USD, extensions, RTX, or Nucleus. Nucleus is a separate service (often a CPU instance + persistent disk), not something to co-host on the GPU workstation unless this is a tiny lab.

---

## Slide 19 — Section: References

# References

---

## Slide 20 — References

# REFERENCES

| Topic | Link |
|-------|------|
| CUDA downloads (Win x64, local exe) | https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local |
| Omniverse Kit (NGC) | https://catalog.ngc.nvidia.com/orgs/nvidia/teams/omniverse/collections/kit |
| Enterprise Nucleus Server | https://catalog.ngc.nvidia.com/orgs/nvidia/teams/omniverse/collections/enterprise-nucleus/artifacts |
| kit-app-template | https://github.com/NVIDIA-Omniverse/kit-app-template |
| EC2 G5 (A10G) | https://aws.amazon.com/ec2/instance-types/g5/ |
| On-Demand G/VT quota | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-on-demand-instances.html |
| NVIDIA drivers on Windows EC2 | https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/install-nvidia-driver.html |
| Azure N-series Windows drivers | https://learn.microsoft.com/en-us/azure/virtual-machines/windows/n-series-driver-setup |

---

## Slide 21 — Close

Thank you.

---

## Ops appendix (not in the original 21 slides)

Use this if the customer asks “how would we run this in production?”

- **Quota first**, then AMI, then instance. IaC cannot skip Service Quotas.  
- **Pin** Region + AZ with G5 capacity; consider Capacity Reservation for a workshop date.  
- **Stop** G5 when idle — A10G On-Demand is expensive; instance store is wiped on stop for some topologies — keep USD on **EBS**.  
- **Nucleus** on a non-GPU instance with backups; Kit clients on G5.  
- **Do not** put RDP on a public IP without CIDR lock + MFA jump host.  
- Snapshot / AMI the golden image **after** GRID + CUDA 13.2 + Kit build succeed.

### First-run validation checklist

- [ ] `Running On-Demand G and VT instances` quota ≥ instance vCPUs in the target Region  
- [ ] Instance is `g5.2xlarge` or `g5.4xlarge` and `running`  
- [ ] SG: RDP only from corp/VPN  
- [ ] GRID driver installed; reboot done  
- [ ] `nvidia-smi` shows **A10G**  
- [ ] CUDA Toolkit **13.2**; `nvcc --version`  
- [ ] `kit-app-template` cloned, `.\repo.bat build` / `launch` succeeds  
- [ ] Kit UI loads; RTX viewport available  
