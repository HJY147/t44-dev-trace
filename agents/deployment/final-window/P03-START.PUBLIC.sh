umask 077
# Root must separately create the fresh actual LOAD readiness receipt and substitute its exact raw SHA.
# Receipt schema: root_approved=true, actual_LOAD_ready=true, observed_utc=actual-new-UTC,
# actual_image_id=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1,
# QA_or_other_writer_started=false, original_live_python_proof_sha256=actual-current-proof.
# This command intentionally requires the explicit SHA as positional argument.
[ "$#" -eq 1 ] || exit 2
systemd-run --unit=t44-final-p03-continuous --property=Type=exec --property=UMask=0077 --property=RuntimeMaxSec=2400 --collect python3 /root/t44-final-20261029/ops01/deployment/cloud-reuse/P03-CONTINUOUS.PUBLIC.py --load-ready /root/t44-final-20261029/P03-LOAD-READY.PUBLIC.json --load-ready-sha256 "$1" --cost-approval /root/t44-final-20261029/F03-COST-APPROVAL.PUBLIC.json --cost-approval-sha256 e1857a84837a90591ce3c9e4b17c2270204ba85fc59ad17f144ef471c95cdb59
