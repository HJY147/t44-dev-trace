"""Exact final wrapper tests plus actual final producer CLI through staged paths to a DB sentinel."""
import ast,contextlib,copy,hashlib,importlib.util,json,subprocess,sys,types,unittest
from datetime import UTC,datetime,timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
DEPLOY=HERE.parents[2]/"deployment-preparation-r30"
BACKEND="3be27131398a049f1a509918e5308f1bda7c8cec"
WRAPPER="8c73486440720506357ffa90efdb5b59cdd91028"
MANIFEST="66ab164258803a8a62edfc3dbc713837431ce8b649664ab8de4c5a48a2359606"

def git(ref,path):return subprocess.check_output(["git","show",ref+":"+path])
def load_raw(raw,name,path):
    m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
    exec(compile(raw,str(path),"exec"),m.__dict__);return m

wraw=git(WRAPPER,"deployment/cloud-reuse/r30-neutral-admin.py")
assert hashlib.sha256(wraw).hexdigest()=="8e9d024b7aa38692a633b620a23a27380d155ed7a8725f45c9ee25dac0fe4d9a"
W=load_raw(wraw,"review_final_wrapper",DEPLOY/"deployment/cloud-reuse/r30-neutral-admin.py")
testpath="tmp/758_deployment_neutral_admin_r30/test_admin_wrapper.py"
text=git(WRAPPER,testpath).decode()
text=text.replace("ROOT = Path(__file__).resolve().parents[2]","ROOT = Path("+repr(str(DEPLOY))+")")
text=text.replace('W = load(ROOT / "deployment/cloud-reuse/r30-neutral-admin.py", "neutral_admin_wrapper")',"W = EXACT_WRAPPER")
text=text.replace("0a34a81e9fb59abf6c500f5acbe284c053d1f903",BACKEND).replace("7c9d08a6b1b521dfb2046c8354686e367354d81f69c0813eb3ccfad42cfe841d",MANIFEST)
case=types.ModuleType("review_final_owner_cases");case.__file__=str(HERE/"wrapper_cases.py");case.EXACT_WRAPPER=W
sys.modules[case.__name__]=case;exec(compile(text,WRAPPER+"/test_admin_wrapper.py","exec"),case.__dict__)
bridge_record={}

def bridge(self):
    args=self.setup_phase();_,value,g,budget,phase_binding,identity,sample=self.context
    value.update(source_manifest_sha256="0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b",upgrade_binding_sha256="b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345",cryptographic_transport_proofs={"synthetic":True},tls={"synthetic":True},app_private_ip="10.0.0.1",tls_port=26445)
    def replace(path,obj):path.unlink();W.save(path,obj)
    replace(args.phase_dir/"binding.json",value);args.binding_sha256=W.digest((args.phase_dir/"binding.json").read_bytes())
    probe=json.loads(args.budget_receipt.read_bytes());probe["binding_sha256"]=args.binding_sha256
    replace(args.budget_receipt,probe);args.budget_receipt_sha256=W.digest(args.budget_receipt.read_bytes())
    code=args.output_dir.parent/"exact-producer";code.mkdir(mode=0o700)
    mr=git(BACKEND,"agents/backend/neutral-r30/code-manifest.PUBLIC.json");assert W.digest(mr)==MANIFEST
    declared=json.loads(mr)
    for name,digest in declared["files"].items():
        data=git(BACKEND,"agents/backend/neutral-r30/"+name);assert W.digest(data)==digest and len(data)==declared["file_sizes"][name];W.write(code/name,data)
    W.write(code/"code-manifest.PUBLIC.json",mr);args.code_dir=code;args.code_manifest=code/"code-manifest.PUBLIC.json";args.code_manifest_sha256=MANIFEST
    plan=json.loads((code/"plan.template.PUBLIC.json").read_bytes())
    end=datetime.fromisoformat(value["stop_utc"].replace("Z","+00:00"));t0=end-timedelta(minutes=35);now=datetime.now(UTC)
    stamp=lambda v:v.isoformat().replace("+00:00","Z")
    plan.update(root_admit_preparation=True,run_id="r30window01",namespace=value["project"],authorized_project_ids=list(range(1,41)),allowed_writes=["seed_demo","init-user","service-token","login","createTask","transitionTask","createEscalation"])
    plan["target"].update(compose_project=value["project"],database=value["database"],mysql_user=value["database"]+"_app",binding_sha256=args.binding_sha256,origin="https://10.0.0.1:26445",connect_ip="10.0.0.1",ca_sha256=W.digest(b"synthetic-ca"))
    plan["gen_binding"].update(path="/neutral-input/binding.json",sha256=args.binding_sha256)
    plan["window"].update(start_utc=stamp(t0+timedelta(minutes=20)),end_utc=stamp(t0+timedelta(minutes=33)),stop_utc=value["stop_utc"])
    plan["lifecycle"].update(t0_utc=stamp(t0),cost_stop_utc=stamp(t0+timedelta(minutes=40)),packet_cutoff_utc=stamp(t0+timedelta(minutes=17,seconds=30)))
    plan["seed"].update(seed=44,anchor_utc=stamp(now-timedelta(days=1)))
    for role,r in plan["runtime_roles"].items():r.update(running_observed=True,receipt_sha256=W.digest(role.encode()))
    for key in ["source","images","transfer","preflight"]:plan["readiness"][key].update(sha256=W.digest(key.encode()),completed_at=stamp(now-timedelta(seconds=90)))
    plan["readiness"].update(all_ready_at=stamp(now-timedelta(seconds=60)),fixture_ready_at=stamp(now-timedelta(seconds=10)),admin_preserves_image_pythonpath=True)
    imported=dict(kind="r30-backend-import-receipt-v1",source_sha=W.SOURCE,bundle_manifest_sha256=plan["source"]["bundle_manifest_sha256"],source_manifest_sha256=plan["source"]["manifest_sha256"],full_runtime_files=60,identity={"config_id":W.CONFIG},package_resolution={"synthetic_not_actual_loaded":True},business_services_started=False,volumes_modified=False)
    replace(args.import_receipt,imported)
    plan["source"].update(actual_loaded_receipt_sha256=W.digest(args.import_receipt.read_bytes()),actual_loaded_receipt_path=str(args.import_receipt),actual_loaded_observed_at=stamp(now-timedelta(seconds=30)),actual_loaded_full_chain_reviewed_by_root=True)
    plan["budget"]["actual_admission_receipt_sha256"]=args.budget_receipt_sha256
    replace(args.plan,plan)
    intent=json.loads(args.intent.read_bytes());intent.update(binding_sha256=args.binding_sha256,operation="counts");replace(args.intent,intent)
    original_inputs={p:p.read_bytes() for p in [args.plan,args.intent,args.import_receipt,args.budget_receipt,args.phase_dir/"binding.json"]}
    owner_calls=[];child=[];seen=[]
    original_methods={n:getattr(Path,n) for n in ["open","stat","lstat"]}
    def mapped(p):
        s=str(p)
        for prefix,name in [("/neutral-input/","inputs"),("/neutral-code/","code"),("/neutral-output/","output")]:
            if s.startswith(prefix):return args.output_dir/name/s[len(prefix):]
        return p
    def open_(p,*a,**k):return original_methods["open"](mapped(p),*a,**k)
    def stat_(p,*a,**k):return original_methods["stat"](mapped(p),*a,**k)
    def lstat_(p,*a,**k):return original_methods["lstat"](mapped(p),*a,**k)
    class DBBoundary(RuntimeError):pass
    def runner(argv,out,err,stdin,timeout,env,cleanup):
        self.lock_held();child.append(argv);assert stdin is None
        assert argv[argv.index("--user")+1]=="10001:10001"
        for n in ["guard","http_primitives","admin_seed","admin"]:load_raw((args.output_dir/"code"/(n+".py")).read_bytes(),n,args.output_dir/"code"/(n+".py"))
        mysql=SimpleNamespace(database=value["database"],host="mysql",port=3306,username=value["database"]+"_app")
        persistence=types.ModuleType("t44.persistence");persistence.SqlAlchemyUnitOfWorkFactory=lambda v:v
        def connect(v):seen.append("actual producer CLI reached correct DB boundary");raise DBBoundary()
        persistence.create_mysql_engine=connect
        settings=types.ModuleType("t44.settings");settings.Settings=SimpleNamespace(from_env=lambda:SimpleNamespace(mysql_settings=lambda:mysql))
        common=types.ModuleType("t44.services.common");common.wire=lambda v:v
        parser_args=argv[argv.index("credential-admin")+3:]
        with patch.object(Path,"open",open_),patch.object(Path,"stat",stat_),patch.object(Path,"lstat",lstat_),patch.dict(sys.modules,{"t44.persistence":persistence,"t44.settings":settings,"t44.services.common":common}),patch.object(sys,"argv",["/neutral-code/admin.py",*parser_args]):
            try:sys.modules["admin"].main()
            except DBBoundary:pass
            else:raise AssertionError("real staged producer CLI did not reach DB boundary")
        self.lock_held();W.write(out,b"synthetic no DB counts\n");W.write(err,b"")
        result=args.output_dir/"output/result";result.mkdir(mode=0o700);W.save(result/"counts.json",{"synthetic":True})
        return 0
    def module(path,expected):W.pinned(path,expected);return g
    def measure(v,live):self.lock_held();return identity,sample,budget.checked_plan(v)
    with patch.object(W,"require_host"),patch.object(W,"container_owner",side_effect=lambda p:owner_calls.append(str(p))),patch.object(W,"private_result"),patch.object(W,"module",side_effect=module),patch.object(g,"phase_binding",side_effect=phase_binding),patch.object(g,"budget_module",return_value=budget),patch.object(budget,"measure",side_effect=measure),patch.object(budget,"verify_runtime_environment",return_value=[]):
        result=W.run_admin(args,runner=runner)
    assert len(seen)==len(child)==1 and len(owner_calls)>=7
    assert all(p.read_bytes()==raw for p,raw in original_inputs.items())
    fields=set()
    guardtree=ast.parse((code/"guard.py").read_text())
    for n in ast.walk(guardtree):
        if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=="binding" and isinstance(n.slice,ast.Constant):fields.add(n.slice.value)
    fields.update(["config_ids","image_ids","cryptographic_transport_proofs","tls","file_hashes"])
    gentree=ast.parse((self.profile_dir/"generation.py").read_text())
    bindingdict=next(n.value for n in ast.walk(gentree) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="binding" for t in n.targets))
    actualfields={k.value for k in bindingdict.keys};assert fields<=actualfields and len(fields)==16 and "crypto_transport_proofs" not in fields
    bridge_record.update(actual_manifest=MANIFEST,actual_producer=BACKEND,staged_files=len(declared["files"]),actual_admin_CLI_reached_fake_DB_boundary=True,container_binding_path="/neutral-input/binding.json",original_host_bytes_unchanged=True,binding_required_fields=sorted(fields),actual_GEN_fields=len(actualfields),UID10001_argv_and_chown_calls=len(owner_calls),ownership_syscalls_are_explicit_test_seams=True,real9e_flock_and_admit_remeasure=True,actual_Docker_SQL_cloud_HTTP_sessions=False)

case.AdminWrapper.test_final_exact_producer_real_CLI_bridge=bridge
suite=unittest.defaultTestLoader.loadTestsFromModule(case)
with (HERE/"final-chain-review.log").open("w") as log:r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
record=dict(wrapper=WRAPPER,producer=BACKEND,manifest=MANIFEST,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),bridge=bridge_record,owner_old_manifest_test_parameter_updated_to_exact_final_only=True)
(HERE/"final-chain-review.json").write_text(json.dumps(record,indent=2)+"\n")
assert r.wasSuccessful() and r.testsRun==11
print(json.dumps(record))
