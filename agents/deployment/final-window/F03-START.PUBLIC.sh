umask 077
sha256sum /root/t44-final-20261029/F03-COST-APPROVAL.PUBLIC.json
systemd-run --unit=t44-final-f03-continuous --property=Type=exec --property=UMask=0077 --property=RuntimeMaxSec=2400 --collect python3 /root/t44-final-20261029/ops01/deployment/cloud-reuse/F03-CONTINUOUS.PUBLIC.py --package /root/t44-final-20261029/boot01/official --app-ip 172.21.182.245 --run-id r30finalf03 --output /root/t44-final-20261029/F03 --cost-approval /root/t44-final-20261029/F03-COST-APPROVAL.PUBLIC.json --cost-approval-sha256 e1857a84837a90591ce3c9e4b17c2270204ba85fc59ad17f144ef471c95cdb59
