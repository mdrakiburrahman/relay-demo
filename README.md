# Azure Relay Hybrid Connection Demo

Two Python apps — `server.py` (cloud-side listener) and `client.py` (local sender) — rendezvoused through an Azure Relay Hybrid Connection over websockets.

## 1. One-time Azure setup (PowerShell)

```powershell
$SUB  = "ce859648-30e1-4135-9d0f-8358aebfe789"
$RG   = "arc-dev-relay"
$NS   = "mdrrahman-dev-relay"
$HC   = "demo"
$RULE = "demo-listen-send"

az account set --subscription $SUB
az relay hyco create -g $RG --namespace-name $NS -n $HC --requires-client-authorization true 2>$null
az relay hyco authorization-rule create -g $RG --namespace-name $NS --hybrid-connection-name $HC -n $RULE --rights Listen Send 2>$null
$KEY = az relay hyco authorization-rule keys list -g $RG --namespace-name $NS --hybrid-connection-name $HC -n $RULE --query primaryKey -o tsv
[ordered]@{ namespace=$NS; path=$HC; keyrule=$RULE; key=$KEY } | ConvertTo-Json | Out-File -Encoding utf8 config.json
```

## 2. Run

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Terminal 1:

```powershell
.\venv\Scripts\Activate.ps1
python server.py
```

Terminal 2:

```powershell
.\venv\Scripts\Activate.ps1
python client.py
```

Type a message at the client prompt and watch it arrive on the server.
