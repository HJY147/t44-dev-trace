set -eu
python3 -B /root/t44-r9/resume-20261028-01/resource_window.py --raw /root/t44-r9/resource-mirror-r28p16-02/app-raw.jsonl --sha256 045fa2e0340f1ea2e04794da93267025895fb43df855803f7b10406d062beee1 --begin 2026-10-28T09:47:52.170963+00:00 --end 2026-10-28T09:48:07.315662+00:00
python3 -B /root/t44-r9/resource-mirror-r28p16-02/controller.py stop --directory /root/t44-r9/resource-mirror-r28p16-02 --binding-sha256 97497b2d935ac0c443c8825caf84af9cf351f89a993948598d4424f6b48cf27d
