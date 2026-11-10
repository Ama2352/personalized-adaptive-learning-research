import io,json,zipfile,hashlib,base64,traceback
try:
    assert INTEGRATION04_PROC.poll() is not None,'integration04 process still running'
    entries={}
    for number in range(1,5):
        folder=ROOT/f'integration-evidence{number:02d}'
        status=json.loads((folder/'status.json').read_text())
        assert 'elapsed_seconds' in status,'nonterminal attempt'
        for name in ['STARTED.json','status.json','sources.json','stdlib.log','stdlib.xml','no-torch.log','no-torch.xml','remaining.log','remaining.xml']:
            p=folder/name
            assert p.is_file() and p.stat().st_size<32*1024*1024
            entries[f'attempt{number:02d}/'+name]=p.read_bytes()
    for number in [3,4]:
        p=ROOT/f'artifacts/akt/tmp/integration{number:02d}-driver.log'
        entries[f'driver{number:02d}.log']=p.read_bytes()
    entries['runtime.json']=(ROOT/'colab-evidence/runtime.json').read_bytes()
    assert sum(len(v) for v in entries.values())<96*1024*1024
    inventory={name:hashlib.sha256(data).hexdigest() for name,data in entries.items()}
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in entries.items():z.writestr(name,data)
        z.writestr('SHA256.json',json.dumps(inventory,indent=2))
    INTEGRATION_EXPORT=b.getvalue()
    INTEGRATION_EXPORT_PARTS=[base64.b64encode(INTEGRATION_EXPORT[i:i+24000]).decode('ascii') for i in range(0,len(INTEGRATION_EXPORT),24000)]
    print(json.dumps(dict(integration_export=True,bytes=len(INTEGRATION_EXPORT),sha256=hashlib.sha256(INTEGRATION_EXPORT).hexdigest(),parts=len(INTEGRATION_EXPORT_PARTS),files=len(entries),raw_bytes=sum(len(v) for v in entries.values()))))
except BaseException:
    print(traceback.format_exc(),flush=True)
