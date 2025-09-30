# Disk and LVM Extension Guide (`/dev/sda` example)

> **Important**: Ensure a full backup is made before proceeding. Run all commands as `root` or with `sudo`.

---

## 1. Resize the partition (`/dev/sda3` assumed)

This assumes that the physical or virtual disk has already been expanded (e.g. via hypervisor or physical upgrade).

### 1.1 Launch `parted`

```bash
parted /dev/sda
1.2 Inside parted, check existing partitions:
bash
Copy code
(parted) print
Look for the partition that contains LVM — it usually has the lvm flag, e.g.:

pgsql
Copy code
Number  Start   End     Size    File system  Name  Flags
 3      1075MB  700GB   699GB                lvm
Make sure to note the correct partition number (e.g. 3 for /dev/sda3).

1.3 Resize the partition
bash
Copy code
(parted) resizepart 3 100%
Replace 3 with the actual partition number you found in the print output.

1.4 Exit parted
bash
Copy code
(parted) quit
2. Refresh the partition table
bash
Copy code
partprobe
This informs the OS of the updated partition layout.

3. Verify the updated partition size
bash
Copy code
lsblk
Ensure that /dev/sda3 is now larger than before.

4. Resize the LVM physical volume
bash
Copy code
pvresize /dev/sda3
This allows LVM to use the new free space in the partition.

5. Check available space in VG and PV
bash
Copy code
vgs
pvs
These show the free space now available for use in the volume group.

6. Extend the thin pool (if using thin provisioning)
Optional, only if you're using a thin pool like /dev/almalinux/pool00.

bash
Copy code
lvextend -l +100%FREE /dev/almalinux/pool00
This command extends the thin pool to use all available free space in the volume group.

7. Extend the logical volume
Option A: Extend /var by 100 GB
bash
Copy code
lvextend -L +100G /dev/almalinux/var
Option B: Extend /var/log by 2 GB
bash
Copy code
lvextend -L +2G /dev/almalinux/var_log
You can also use -l +100%FREE if you want to allocate all available space, but it's not recommended unless you're sure.

8. Resize the filesystem
For /var:
bash
Copy code
xfs_growfs /var
For /var/log:
bash
Copy code
xfs_growfs /var/log
Incorrect: /var/_log — this is a typo.
Correct: /var/log

To check the filesystem type:

bash
Copy code
df -T /var/log
If it's ext4, use:

bash
Copy code
resize2fs /dev/almalinux/var_log
9. Final verification
bash
Copy code
df -h
lsblk
Ensure that the logical volumes and filesystems reflect the new size.

Summary – Final Command List
bash
Copy code
parted /dev/sda
# Inside parted:
# print
# resizepart <partition_number> 100%
# quit

partprobe
lsblk

pvresize /dev/sda3
vgs
pvs

lvextend -l +100%FREE /dev/almalinux/pool00

# Option A
lvextend -L +100G /dev/almalinux/var
xfs_growfs /var

# Option B
lvextend -L +2G /dev/almalinux/var_log
xfs_growfs /var/log

df -h
lsblk
This document covers disk, LVM, and filesystem expansion on systems using XFS and LVM thin provisioning.

yaml
Copy code
