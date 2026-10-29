umask 077
# Only after actual F03 fixture/environment success; never regenerate prior private sessions.
[ -f /root/t44-final-20261029/F03/functional-environment.private.json ] || exit 2
systemd-run --unit=t44-final-f03-transport-v2 --property=Type=exec --property=UMask=0077 --property=RuntimeMaxSec=1800 --collect python3 /root/t44-final-20261029/ops01/deployment/cloud-reuse/F03-TRANSPORT-APP.PUBLIC.py --f-dir /root/t44-final-20261029/F03 --load-ip 172.21.182.244 --load-public-key /root/t44-final-20261029/ops01/qa-public/load-public.pem
