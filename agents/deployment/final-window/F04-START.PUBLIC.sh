umask 077
# Root creates a NEW exact public approval from actual resume evidence; parameter1 is its SHA.
# root_approved:true, remaining_budget_CNY:40, historical_APP_first_boot_utc:'2026-10-29T13:45:26Z',
# resume_observed_utc:actual root authorization timestamp before resume,
# actual_APP_resume_boot_utc:actual new kernel boot, actual_LOAD_resume_boot_utc:actual new kernel boot,
# absolute_cost_cutoff_utc:'2026-10-29T19:30:00Z'. No old approval or T0 is reused.
[ "$#" -eq 1 ] || exit 2
systemd-run --unit=t44-final-f04-continuous --property=Type=exec --property=UMask=0077 --property=RuntimeMaxSec=2400 --collect python3 /root/t44-final-20261029/ops01/deployment/cloud-reuse/F04-CONTINUOUS.PUBLIC.py --package /root/t44-final-20261029/boot01/official --app-ip 172.21.182.245 --run-id r30finalf04 --output /root/t44-final-20261029/F04 --cost-approval /root/t44-final-20261029/RESUME04-COST-APPROVAL.PUBLIC.json --cost-approval-sha256 "$1"
